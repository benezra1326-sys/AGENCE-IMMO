"""Activité Applications : suivi des projets d'apps (ZIV en premier).

Chaque app décrit son avancement dans une fiche d'état (format : apps/README.md) :
- soit écrite dans ce dépôt, `apps/<id>/statut.json` (le back-office la relit toutes les 5 minutes) ;
- soit envoyée au serveur sur POST /api/apps/statut avec l'en-tête X-Jeton = BO_APPS_TOKEN.
La fiche la plus récente (champ maj_le) l'emporte. Un changement notable (étape, statut, blocage,
avancement) prépare une alerte pour le bot Telegram Apps, jamais pour le bot Immobilier.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import alertes
from .config import FUSEAU
from .db import journaliser, maintenant

ETAPES = ["idee", "benchmark", "cadrage", "design", "developpement", "tests", "publication", "en_ligne"]
NOMS_ETAPES = {"idee": "idée", "benchmark": "benchmark", "cadrage": "cadrage", "design": "design",
               "developpement": "développement", "tests": "tests", "publication": "publication sur les stores",
               "en_ligne": "en ligne"}
STATUTS = ("en_cours", "en_pause", "bloque", "termine")
NOMS_STATUTS = {"en_cours": "en cours", "en_pause": "en pause", "bloque": "bloqué", "termine": "terminé"}
SUIVIS = ("etape", "statut", "avancement", "blocages", "prochaine_etape")


class FicheInvalide(ValueError):
    pass


def valider(d):
    """Contrôle et normalise une fiche d'état. Lève FicheInvalide avec un message en français."""
    if not isinstance(d, dict):
        raise FicheInvalide("la fiche doit être un objet JSON")
    aid = str(d.get("id") or "").strip().lower()
    if not aid or not aid.replace("-", "").replace("_", "").isalnum() or len(aid) > 40:
        raise FicheInvalide("id manquant ou invalide (lettres, chiffres, tirets)")
    etape = d.get("etape", "idee")
    if etape not in ETAPES:
        raise FicheInvalide(f"étape inconnue : {etape} (attendu : {', '.join(ETAPES)})")
    statut = d.get("statut", "en_cours")
    if statut not in STATUTS:
        raise FicheInvalide(f"statut inconnu : {statut} (attendu : {', '.join(STATUTS)})")
    try:
        avancement = max(0, min(100, int(d.get("avancement") or 0)))
    except (TypeError, ValueError):
        raise FicheInvalide("avancement : nombre entre 0 et 100") from None
    liste = lambda v: [str(x)[:300] for x in v][:20] if isinstance(v, list) else []  # noqa: E731
    liens = [{"libelle": str(x.get("libelle") or x.get("url"))[:80], "url": str(x["url"])[:500]}
             for x in (d.get("liens") or []) if isinstance(x, dict) and str(x.get("url", "")).startswith("https://")][:10]
    chantiers = [{"nom": str(x["nom"])[:80],
                  "statut": x.get("statut") if x.get("statut") in ("a_faire", "en_cours", "termine", "bloque") else "a_faire",
                  "avancement": _pourcent(x.get("avancement")), "responsable": str(x.get("responsable") or "")[:40] or None}
                 for x in (d.get("chantiers") or []) if isinstance(x, dict) and x.get("nom")][:30]
    historique = [{"quand": str(x.get("quand", ""))[:25], "texte": str(x.get("texte", ""))[:300]}
                  for x in (d.get("historique") or []) if isinstance(x, dict) and x.get("texte")][-30:]
    return {
        "id": aid,
        "nom": str(d.get("nom") or aid.upper())[:60],
        "description": str(d.get("description") or "")[:500],
        "depot": str(d.get("depot") or "")[:120] or None,
        "etape": etape,
        "statut": statut,
        "avancement": avancement,
        "resume": str(d.get("resume") or "")[:1000],
        "prochaine_etape": str(d.get("prochaine_etape") or "")[:300],
        "blocages": liste(d.get("blocages")),
        "agents": liste(d.get("agents")),
        "chantiers": chantiers,
        "liens": liens,
        "historique": historique,
        "maj_le": str(d.get("maj_le") or maintenant())[:25],
    }


def _pourcent(v):
    try:
        return max(0, min(100, int(v or 0)))
    except (TypeError, ValueError):
        return 0


def enregistrer(cx, fiche, source):
    """Enregistre une fiche validée. Renvoie la liste des changements notables (vide si rien de neuf)."""
    f = valider(fiche)
    ancien = cx.execute("SELECT donnees FROM apps WHERE id=?", (f["id"],)).fetchone()
    avant = json.loads(ancien["donnees"]) if ancien else None
    if avant and avant.get("maj_le", "") >= f["maj_le"]:
        return []  # déjà connue, ou plus ancienne que celle enregistrée
    cx.execute(
        """INSERT INTO apps (id, nom, donnees, source, maj_le) VALUES (?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET nom=excluded.nom, donnees=excluded.donnees, source=excluded.source,
             maj_le=excluded.maj_le""",
        (f["id"], f["nom"], json.dumps(f, ensure_ascii=False), source, f["maj_le"]),
    )
    changements = _changements(avant, f)
    journaliser(cx, "apps", "état d'app mis à jour" if avant else "app ajoutée", f["id"],
                "; ".join(changements)[:300] or None)
    if changements:
        alertes.preparer(cx, type="app_maj", canal="telegram_apps", cle=f"app:{f['id']}:{f['maj_le']}",
                         corps=f"{f['nom']} – mise à jour\n" + "\n".join(f"• {c}" for c in changements)
                         + (f"\nProchaine étape : {f['prochaine_etape']}" if f["prochaine_etape"] else ""))
    return changements


def _changements(avant, f):
    if avant is None:
        return [f"Nouveau projet suivi : étape {NOMS_ETAPES[f['etape']]}, {f['avancement']} %"]
    c = []
    if avant.get("etape") != f["etape"]:
        c.append(f"Étape : {NOMS_ETAPES.get(avant.get('etape'), avant.get('etape'))} → {NOMS_ETAPES[f['etape']]}")
    if avant.get("statut") != f["statut"]:
        c.append(f"Statut : {NOMS_STATUTS.get(avant.get('statut'), avant.get('statut'))} → {NOMS_STATUTS[f['statut']]}")
    if avant.get("avancement") != f["avancement"]:
        c.append(f"Avancement : {avant.get('avancement', 0)} % → {f['avancement']} %")
    nouveaux = [b for b in f["blocages"] if b not in (avant.get("blocages") or [])]
    c += [f"Nouveau blocage : {b}" for b in nouveaux]
    if (avant.get("blocages") or []) and not f["blocages"]:
        c.append("Plus aucun blocage")
    return c


def synchroniser(cx, racine_depot, lire_distant=None):
    """Relit apps/*/statut.json, puis la fiche publiée dans le dépôt de chaque app (champ « source »
    de apps/<id>/app.json). Une fiche illisible est signalée dans le journal, jamais ignorée en silence."""
    dossier = Path(racine_depot) / "apps"
    vus = 0
    for f in sorted(dossier.glob("*/statut.json")) if dossier.exists() else []:
        try:
            enregistrer(cx, json.loads(f.read_text(encoding="utf-8")), "depot")
            vus += 1
        except (OSError, ValueError) as e:
            journaliser(cx, "apps", "fiche d'app illisible", str(f.relative_to(racine_depot)), str(e)[:200],
                        niveau="erreur")
    for f in sorted(dossier.glob("*/app.json")) if dossier.exists() and lire_distant else []:
        try:
            src = json.loads(f.read_text(encoding="utf-8")).get("source") or {}
            if src.get("depot") and src.get("chemin"):
                enregistrer(cx, json.loads(lire_distant(src["depot"], src["chemin"])), f"github:{src['depot']}")
                vus += 1
        except Exception as e:  # noqa: BLE001 - réseau, droits, JSON : tout est noté, rien n'arrête le service
            journaliser(cx, "apps", "fiche d'app distante illisible", f.parent.name, f"{type(e).__name__}: {e}"[:200],
                        niveau="erreur")
    return vus


def lecteur_github(jeton=None):
    """Lit un fichier d'un dépôt GitHub (branche par défaut). Jeton nécessaire pour un dépôt privé."""
    import urllib.request

    def lire(depot, chemin):
        req = urllib.request.Request(f"https://api.github.com/repos/{depot}/contents/{chemin}",
                                     headers={"Accept": "application/vnd.github.raw+json", "User-Agent": "backoffice"})
        if jeton:
            req.add_header("Authorization", f"Bearer {jeton}")
        with urllib.request.urlopen(req, timeout=20) as rep:  # noqa: S310 - hôte fixe GitHub
            return rep.read().decode("utf-8")
    return lire


def lister(cx):
    return [json.loads(r["donnees"]) | {"_source": r["source"]}
            for r in cx.execute("SELECT donnees, source FROM apps ORDER BY nom").fetchall()]


def trouver(cx, nom):
    nom = (nom or "").strip().lower()
    return next((a for a in lister(cx) if nom in (a["id"], a["nom"].lower())), None)


def texte_app(a):
    l = [f"{a['nom']} – {NOMS_ETAPES[a['etape']]}, {NOMS_STATUTS[a['statut']]}, {a['avancement']} %"]
    if a["resume"]:
        l.append(a["resume"])
    if a["prochaine_etape"]:
        l.append(f"Prochaine étape : {a['prochaine_etape']}")
    if a["blocages"]:
        l.append("Blocages :\n" + "\n".join(f"• {b}" for b in a["blocages"]))
    l.append(f"Mis à jour le {a['maj_le'][:10]}")
    return "\n".join(l)


def recap(cx, config, maintenant_dt=None):
    now = maintenant_dt or datetime.now(timezone.utc)
    depuis = (now - timedelta(days=1)).isoformat()
    l = [f"Apps – récap du {now.astimezone(FUSEAU).strftime('%d/%m/%Y')}"]
    if config.mode_envoi != "reel":
        l.append("(mode test : aucune alerte n'est réellement envoyée)")
    apps = lister(cx)
    l.append(f"\nProjets suivis : {len(apps)}")
    l += [f"• {a['nom']} : {NOMS_ETAPES[a['etape']]}, {a['avancement']} %, {NOMS_STATUTS[a['statut']]}" for a in apps]
    faites = cx.execute("SELECT titre FROM taches WHERE activite='apps' AND statut='terminee' AND maj_le >= ?",
                        (depuis,)).fetchall()
    l.append(f"\nTâches terminées (24 h) : {len(faites)}")
    l += [f"• {r['titre']}" for r in faites[:8]]
    ouvertes = cx.execute("SELECT COUNT(*) FROM taches WHERE activite='apps' AND statut IN ('en_attente','en_cours')").fetchone()[0]
    l.append(f"Tâches ouvertes : {ouvertes}")
    bloc = [(a["nom"], b) for a in apps for b in a["blocages"]]
    bloc += [("tâche", r["titre"]) for r in cx.execute(
        "SELECT titre FROM taches WHERE activite='apps' AND statut IN ('bloquee','echec')").fetchall()]
    l.append("\nBlocages :" if bloc else "\nAucun blocage.")
    l += [f"• {n} : {b}" for n, b in bloc[:8]]
    return "\n".join(l)
