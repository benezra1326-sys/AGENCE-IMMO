"""Modèle de tâche : création sans doublon, exécution, échec avec reprise automatique.

Cycle : en_attente -> en_cours -> terminee
                               -> en_attente (nouvel essai programmé, délai croissant)
                               -> echec (après max_tentatives) ou bloquee (connexion manquante)
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from .db import journaliser, ligne, maintenant

STATUTS = ("en_attente", "en_cours", "terminee", "echec", "bloquee")


def _id_depuis_cle(cle):
    return "T-" + hashlib.sha1(cle.encode("utf-8")).hexdigest()[:10]


def creer(cx, *, activite, agent, titre, cle_unique, type="manuelle", source=None,
          origine="serveur", max_tentatives=3, donnees=None, statut="en_attente"):
    """Crée une tâche. Si une tâche porte déjà cette clé, la renvoie au lieu d'en créer une autre."""
    existante = cx.execute("SELECT * FROM taches WHERE cle_unique=?", (cle_unique,)).fetchone()
    if existante:
        return ligne(existante), False
    tid = _id_depuis_cle(cle_unique)
    t = maintenant()
    cx.execute(
        """INSERT INTO taches (id, activite, agent, type, titre, statut, source, cree_le, maj_le,
                              cle_unique, origine, max_tentatives, donnees)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tid, activite, agent, type, titre, statut, source, t, t, cle_unique, origine,
         max_tentatives, json.dumps(donnees or {}, ensure_ascii=False)),
    )
    journaliser(cx, agent, "tâche créée", tid, titre)
    return obtenir(cx, tid), True


def obtenir(cx, tid):
    return ligne(cx.execute("SELECT * FROM taches WHERE id=?", (tid,)).fetchone())


def demarrer(cx, tid):
    cur = cx.execute(
        "UPDATE taches SET statut='en_cours', maj_le=? WHERE id=? AND statut='en_attente'",
        (maintenant(), tid),
    )
    return cur.rowcount == 1  # False si déjà prise : évite une double exécution


def terminer(cx, tid, resultat, fichiers=None, cout_eur=0.0):
    cx.execute(
        """UPDATE taches SET statut='terminee', maj_le=?, resultat=?, fichiers=?, cout_eur=cout_eur+?,
                             raison_echec=NULL, prochain_essai=NULL WHERE id=?""",
        (maintenant(), resultat, json.dumps(fichiers or [], ensure_ascii=False), cout_eur, tid),
    )
    if cout_eur:
        cx.execute("INSERT INTO couts (quand, poste, montant_eur, tache_id) VALUES (?,?,?,?)",
                   (maintenant(), "tâche", cout_eur, tid))
    t = obtenir(cx, tid)
    journaliser(cx, t["agent"], "tâche terminée", tid, resultat)


def echouer(cx, tid, raison, *, maintenant_dt=None, bloquante=False):
    """Enregistre un échec. Programme un nouvel essai (2, 4, 8… minutes) tant que possible."""
    t = obtenir(cx, tid)
    tentatives = t["tentatives"] + 1
    now = maintenant_dt or datetime.now(timezone.utc)
    if bloquante:
        statut, prochain = "bloquee", None
    elif tentatives < t["max_tentatives"]:
        statut = "en_attente"
        prochain = (now + timedelta(minutes=2 ** tentatives)).replace(microsecond=0).isoformat()
    else:
        statut, prochain = "echec", None
    cx.execute(
        "UPDATE taches SET statut=?, tentatives=?, raison_echec=?, prochain_essai=?, maj_le=? WHERE id=?",
        (statut, tentatives, raison, prochain, maintenant(), tid),
    )
    journaliser(cx, t["agent"], f"échec ({tentatives}/{t['max_tentatives']}) -> {statut}", tid, raison, niveau="erreur")
    return statut


def reprendre(cx, tid, acteur="avishay"):
    """Reprise manuelle d'une tâche en échec ou bloquée (depuis le tableau de bord ou Telegram)."""
    cur = cx.execute(
        """UPDATE taches SET statut='en_attente', prochain_essai=NULL, tentatives=0, maj_le=?
           WHERE id=? AND statut IN ('echec','bloquee')""",
        (maintenant(), tid),
    )
    if cur.rowcount:
        journaliser(cx, acteur, "reprise demandée", tid)
    return cur.rowcount == 1


def a_executer(cx, maintenant_iso=None):
    now = maintenant_iso or maintenant()
    rows = cx.execute(
        """SELECT * FROM taches WHERE statut='en_attente' AND origine='serveur'
           AND (prochain_essai IS NULL OR prochain_essai <= ?) ORDER BY cree_le""",
        (now,),
    ).fetchall()
    return [ligne(r) for r in rows]


def executer_en_attente(cx, executeurs, maintenant_iso=None):
    """Lance les tâches dont le type a un exécuteur réel. Les autres restent visibles en attente."""
    rapport = []
    for t in a_executer(cx, maintenant_iso):
        fn = executeurs.get(t["type"])
        if fn is None:
            continue
        if not demarrer(cx, t["id"]):
            continue
        try:
            resultat, fichiers, cout = fn(cx, t)
            terminer(cx, t["id"], resultat, fichiers, cout)
            rapport.append((t["id"], "terminee"))
        except ConnexionManquante as e:
            rapport.append((t["id"], echouer(cx, t["id"], str(e), bloquante=True)))
        except Exception as e:  # noqa: BLE001 - toute erreur est enregistrée puis reprise
            rapport.append((t["id"], echouer(cx, t["id"], f"{type(e).__name__}: {e}")))
    return rapport


class ConnexionManquante(Exception):
    """Une connexion nécessaire (Telegram, email, API…) n'est pas configurée : la tâche est bloquée."""
