"""Lecture du registre (activités, agents, connexions, partenaires), des tâches écrites
dans le dépôt (ops/taches/*.json) et des fiches biens (data/biens/*.json).
"""
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import RACINE_BACKOFFICE
from .db import journaliser, ligne, maintenant

REGISTRE = RACINE_BACKOFFICE / "registre"
ORDRE_ETATS = ["prevu", "configure", "teste", "actif", "bloque"]


def _lire(chemin, defaut):
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def nom_agent(agent_id, agents=None):
    """« Victor (Coordination Immo…) » si un prénom existe, sinon l'identifiant."""
    for a in agents if agents is not None else _lire(REGISTRE / "agents.json", {}).get("agents", []):
        if a.get("id") == agent_id:
            return f"{a['prenom']} ({a['nom']})" if a.get("prenom") else a.get("nom", agent_id)
    return agent_id


def charger_registre():
    return {
        "activites": _lire(REGISTRE / "activites.json", {}),
        "agents": _lire(REGISTRE / "agents.json", {}).get("agents", []),
        "connexions": _lire(REGISTRE / "connexions.json", {}),
        "partenaires": _lire(REGISTRE / "partenaires.json", {}).get("partenaires", []),
        "marche": _lire(REGISTRE / "marche.json", {}),
    }


def synchroniser_depot(cx, racine_depot):
    """Importe ou met à jour les tâches décrites dans ops/taches/*.json (une fiche par tâche).

    Clé = id du fichier : relire le même fichier ne crée jamais de doublon.
    Les fichiers illisibles sont signalés dans le journal au lieu d'être ignorés en silence.
    """
    dossier = Path(racine_depot) / "ops" / "taches"
    vus = 0
    for f in sorted(dossier.glob("*.json")) if dossier.exists() else []:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            tid = str(t["id"])
            statut = t.get("statut", "en_attente")
            if statut not in ("en_attente", "en_cours", "terminee", "echec", "bloquee"):
                raise ValueError(f"statut inconnu : {statut}")
        except (OSError, ValueError, KeyError) as e:
            journaliser(cx, "back-office", "fiche tâche illisible", f.name, str(e)[:200], niveau="erreur")
            continue
        try:
            _importer(cx, t, tid, statut)
            vus += 1
        except (sqlite3.Error, TypeError, ValueError) as e:
            journaliser(cx, "back-office", "fiche tâche rejetée", f.name, str(e)[:200], niveau="erreur")
    return vus


def _importer(cx, t, tid, statut):
    cree = t.get("cree_le") or maintenant()
    valeurs = (
        t.get("activite", "immo"), t.get("agent", "coordination"), t.get("titre", tid), statut,
        t.get("source"), cree, t.get("maj_le") or cree, t.get("resultat"),
        json.dumps(t.get("fichiers") or [], ensure_ascii=False), float(t.get("cout_eur") or 0),
        t.get("raison_echec"),
    )
    existante = cx.execute("SELECT maj_le, statut FROM taches WHERE id=?", (tid,)).fetchone()
    if existante is None:
        cx.execute(
            """INSERT INTO taches (activite, agent, titre, statut, source, cree_le, maj_le, resultat, fichiers,
                                  cout_eur, raison_echec, id, cle_unique, origine)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'depot')""",
            (*valeurs, tid, f"depot:{tid}"),
        )
        journaliser(cx, t.get("agent", "coordination"), "tâche importée du dépôt", tid, t.get("titre"))
    elif existante["maj_le"] != valeurs[6] or existante["statut"] != statut:
        cx.execute(
            """UPDATE taches SET activite=?, agent=?, titre=?, statut=?, source=?, cree_le=?, maj_le=?, resultat=?,
                                fichiers=?, cout_eur=?, raison_echec=? WHERE id=?""",
            (*valeurs, tid),
        )
        journaliser(cx, t.get("agent", "coordination"), f"tâche mise à jour ({statut})", tid)
    c = t.get("contenu")
    if isinstance(c, dict):
        cid = c.get("id") or f"C-{tid}"
        ancien = cx.execute("SELECT statut FROM contenus WHERE id=?", (cid,)).fetchone()
        # Une décision prise par Avishay (valide / modification) n'est pas écrasée par le dépôt
        statut_c = c.get("statut", "a_valider")
        if ancien and ancien["statut"] in ("valide", "modification_demandee", "publie") and statut_c == "a_valider":
            statut_c = ancien["statut"]
        cx.execute(
            """INSERT INTO contenus (id, tache_id, activite, titre, format, langue, statut, date_prevue, bien, fichiers, maj_le)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET titre=excluded.titre, format=excluded.format, langue=excluded.langue,
                 statut=excluded.statut, date_prevue=excluded.date_prevue, bien=excluded.bien,
                 fichiers=excluded.fichiers, maj_le=excluded.maj_le""",
            (cid, tid, t.get("activite", "immo"), c.get("titre", t.get("titre")), c.get("format"), c.get("langue"),
             statut_c, c.get("date_prevue"), c.get("bien"),
             json.dumps(c.get("fichiers") or t.get("fichiers") or [], ensure_ascii=False), maintenant()),
        )


def charger_biens(racine_depot):
    dossier = Path(racine_depot) / "data" / "biens"
    biens = []
    for f in sorted(dossier.glob("*.json")) if dossier.exists() else []:
        if f.name == "registre.json":  # table de correspondance interne, pas une fiche
            continue
        b = _lire(f, None)
        if isinstance(b, dict) and b.get("ref"):
            b["_fichier"] = str(f.relative_to(racine_depot))
            biens.append(b)
    return biens


def _motif(texte):
    """« Aloha 40 » couvre aussi Aloha40, aloha-40, ALOHA_40."""
    morceaux = re.findall(r"[A-Za-zÀ-ÿ]+|\d+", texte or "")
    return re.compile(r"[\s_\-]*".join(map(re.escape, morceaux)), re.IGNORECASE) if morceaux else None


def masquer_biens(etat, racine_depot):
    """Le tableau de bord n'affiche que la référence interne AB-NNNN :
    jamais le nom de la propriété ni la référence du partenaire (demande d'Avishay, 9 novembre 2026)."""
    dossier = Path(racine_depot) / "data" / "biens"
    sources = [b for b in etat.get("biens", [])] + charger_biens(racine_depot)  # relu sur disque : masquage répétable
    sources += _lire(dossier / "registre.json", {}).get("biens", []) if dossier.exists() else []
    motifs = []
    for b in sources:
        ref = b.get("ref")
        if not ref:
            continue
        for brut in (b.get("nom"), b.get("ref_partenaire")):
            m = _motif(brut)
            if m:
                motifs.append((m, ref))
    motifs.sort(key=lambda x: -len(x[0].pattern))

    def texte(v):
        for m, ref in motifs:
            v = m.sub(ref, v)
        return v

    def parcourir(v, cle=None):
        if isinstance(v, str):
            return texte(v)
        if isinstance(v, list):
            if cle == "fichiers":  # le lien garde le vrai chemin, seul le libellé est masqué
                return [{"chemin": f, "libelle": texte(f)} if isinstance(f, str) else f for f in v]
            return [parcourir(x) for x in v]
        if isinstance(v, dict):
            return {k: parcourir(x, k) for k, x in v.items()}
        return v

    for b in etat.get("biens", []):
        b.pop("nom", None)
        b.pop("ref_partenaire", None)
    return parcourir(etat) if motifs else etat


def etats_agents(cx, agents):
    """État affiché = état déclaré, relevé à « testé » seulement si une tâche réelle a abouti."""
    resultat = []
    for a in agents:
        a = dict(a)
        stats = {s: 0 for s in ("en_attente", "en_cours", "terminee", "echec", "bloquee")}
        for r in cx.execute("SELECT statut, COUNT(*) n FROM taches WHERE agent=? GROUP BY statut", (a["id"],)):
            stats[r["statut"]] = r["n"]
        a["taches"] = stats
        derniere = cx.execute(
            "SELECT id, titre, maj_le FROM taches WHERE agent=? AND statut='terminee' ORDER BY maj_le DESC LIMIT 1",
            (a["id"],)).fetchone()
        a["etat_declare"] = a["etat"]
        if derniere and a["etat"] in ("prevu", "configure"):
            a["etat"] = "teste"
            a["preuve"] = f"Tâche « {derniere['titre']} » terminée le {derniere['maj_le'][:10]}"
        resultat.append(a)
    return resultat


def etat_complet(cx, config):
    reg = charger_registre()
    rows = lambda q, *p: [ligne(r) for r in cx.execute(q, p).fetchall()]  # noqa: E731
    prospects = rows("SELECT * FROM prospects ORDER BY maj_le DESC LIMIT 200")
    for p in prospects:
        p["historique"] = rows("SELECT canal, sens, texte, cree_le FROM interactions WHERE prospect_id=? ORDER BY id", p["id"])
        p["alertes"] = rows("SELECT type, canal, statut, cree_le FROM alertes WHERE prospect_id=? ORDER BY id", p["id"])
    contenus = rows("SELECT * FROM contenus ORDER BY COALESCE(date_prevue, maj_le)")
    for c in contenus:
        c["retours"] = rows("SELECT decision, texte, canal, cree_le FROM retours WHERE contenu_id=? ORDER BY id", c["id"])
    debut_mois = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    hier = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    total = lambda q, *p: (cx.execute(q, p).fetchone()[0] or 0)  # noqa: E731
    etat = {
        "genere_le": maintenant(),
        "mode_envoi": config.mode_envoi,
        "service": {
            "telegram": config.telegram_configure,
            "email": config.email_configure,
            "api_modeles": config.anthropic_cle_presente,
        },
        "maitre": reg["activites"].get("maitre"),
        "activites": reg["activites"].get("activites", []),
        "agents": etats_agents(cx, reg["agents"]),
        "taches": rows("SELECT * FROM taches ORDER BY maj_le DESC LIMIT 300"),
        "contenus": contenus,
        "prospects": prospects,
        "partenaires": reg["partenaires"],
        "marche": reg["marche"],
        "biens": charger_biens(config.racine_depot),
        "connexions": reg["connexions"],
        "alertes": rows("SELECT id, type, canal, statut, sujet, corps, destinataire, erreur, cree_le FROM alertes ORDER BY id DESC LIMIT 100"),
        "journal": rows("SELECT * FROM journal ORDER BY id DESC LIMIT 300"),
        "couts": {
            "mois_eur": round(total("SELECT SUM(montant_eur) FROM couts WHERE quand >= ?", debut_mois), 2),
            "jour_eur": round(total("SELECT SUM(montant_eur) FROM couts WHERE quand >= ?", hier), 2),
            "lignes": rows("SELECT * FROM couts ORDER BY id DESC LIMIT 100"),
        },
        "erreurs": rows("SELECT * FROM journal WHERE niveau='erreur' ORDER BY id DESC LIMIT 100"),
    }
    return masquer_biens(etat, config.racine_depot)
