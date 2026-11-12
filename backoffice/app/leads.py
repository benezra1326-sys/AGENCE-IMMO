"""Réception des demandes immobilières : fiche prospect, historique, anti-doublon, alertes.

Règles (brief d'Avishay, 9 novembre 2026) :
1. Toute nouvelle demande déclenche immédiatement une alerte Telegram, un email à l'adresse
   professionnelle et la création de la fiche.
2. Une demande explicite d'appel remonte tout de suite, sans attendre la qualification.
3. Les messages suivants enrichissent la fiche sans répéter les mêmes alertes.

L'extraction ci-dessous est volontairement simple (mots-clés, sans IA). La qualification
conversationnelle par un agent viendra quand un modèle sera branché sur le serveur.
"""
import hashlib
import re

from . import alertes
from .db import journaliser, ligne, maintenant

MOTIFS_APPEL = re.compile(
    r"\b(appel(ez|er)?[- ]moi|appelez|m'appeler|rappel(ez|er)[- ]?moi|me rappeler|un appel|"
    r"call me|give me a call|phone call|can you call|could you call|ring me|"
    r"ll[aá]m(a|e)me|llamada|me puede llamar|puede llamarme)\b",
    re.IGNORECASE,
)

PROJETS = {
    "residence_secondaire": r"r[ée]sidence secondaire|holiday home|second home|segunda residencia|vacances",
    "investissement_locatif": r"locatif|rental|rent(al)? investment|alquiler|rendement|yield",
    "renovation_revente": r"r[ée]nov|flip|reform",
    "terrain": r"terrain|plot|land|parcela|solar",
    "hotel": r"h[ôo]tel",
}

ZONES = ["Cabopino", "Marbella", "Nueva Andalucía", "Nueva Andalucia", "Golden Mile", "Puerto Banús",
         "Benahavís", "Benahavis", "Estepona", "Casares", "Sierra Blanca", "La Zagaleta", "Aloha"]


def normaliser_email(e):
    return e.strip().lower() if e and "@" in e else None


def normaliser_tel(t):
    if not t:
        return None
    chiffres = re.sub(r"[^\d+]", "", t)
    if chiffres.startswith("00"):
        chiffres = "+" + chiffres[2:]
    return chiffres if len(re.sub(r"\D", "", chiffres)) >= 8 else None


def normaliser_compte(canal, compte):
    return f"{canal}:{compte.strip().lstrip('@').lower()}" if compte else None


def extraire(texte):
    """Extraction simple d'informations de qualification dans un message libre."""
    info = {}
    if not texte:
        return info
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(millions?|M€|m€|M|Mio)(?![\w²])", texte)
    k = re.search(r"(\d{3,4})\s*(?:k|K)(?:€|\s*eur)?(?!\w)|(\d{3})[ .]000\s*(?:€|eur)", texte)
    if m:
        info["budget"] = f"{m.group(1).replace(',', '.')} M€"
    elif k:
        info["budget"] = f"{k.group(1) or k.group(2)} k€"
    for projet, motif in PROJETS.items():
        if re.search(motif, texte, re.IGNORECASE):
            info["projet"] = projet
            break
    for z in ZONES:
        if z.lower() in texte.lower():
            info["zone"] = z
            break
    info["appel_demande"] = bool(MOTIFS_APPEL.search(texte))
    return info


def _trouver(cx, cles):
    for c in cles:
        row = cx.execute("SELECT prospect_id FROM identifiants WHERE valeur=?", (c,)).fetchone()
        if row:
            return row["prospect_id"]
    return None


def recevoir(cx, config, *, canal, message_id, texte, nom=None, email=None, telephone=None,
             compte=None, langue=None, pays=None, fictif=False):
    """Traite un message entrant. Renvoie un résumé de ce qui a été fait."""
    cle_message = f"{canal}:{message_id}"
    if cx.execute("SELECT 1 FROM interactions WHERE cle_unique=?", (cle_message,)).fetchone():
        return {"resultat": "doublon_message", "prospect_id": None, "alertes": 0}

    identifiants = [(normaliser_email(email), "email"), (normaliser_tel(telephone), "telephone"),
                    (normaliser_compte(canal, compte), "compte")]
    identifiants = [(v, g) for v, g in identifiants if v]
    if not identifiants:
        identifiants = [(cle_message, "message")]

    info = extraire(texte)
    t = maintenant()
    pid = _trouver(cx, [v for v, _ in identifiants])
    nouveau = pid is None
    nb_alertes = 0

    cx.execute("BEGIN IMMEDIATE")
    try:
        if nouveau:
            pid = "P-" + hashlib.sha1(identifiants[0][0].encode()).hexdigest()[:8]
            cx.execute(
                """INSERT INTO prospects (id, type, nom, source, pays, langue, budget, zone, projet, statut,
                                          appel_demande, fictif, cree_le, maj_le)
                   VALUES (?, 'acheteur', ?, ?, ?, ?, ?, ?, ?, 'nouveau', 0, ?, ?, ?)""",
                (pid, nom, canal, pays, langue, info.get("budget"), info.get("zone"), info.get("projet"),
                 int(fictif), t, t),
            )
            journaliser(cx, "acheteurs", "fiche prospect créée", pid, f"source {canal}")
        else:
            # Enrichit seulement les champs vides : on n'écrase pas une info déjà confirmée
            p = ligne(cx.execute("SELECT * FROM prospects WHERE id=?", (pid,)).fetchone())
            maj = {k: v for k, v in {"nom": nom, "pays": pays, "langue": langue, "budget": info.get("budget"),
                                     "zone": info.get("zone"), "projet": info.get("projet")}.items()
                   if v and not p.get(k)}
            if maj:
                sets = ", ".join(f"{k}=?" for k in maj)
                cx.execute(f"UPDATE prospects SET {sets}, maj_le=? WHERE id=?", (*maj.values(), t, pid))
                journaliser(cx, "acheteurs", "fiche enrichie", pid, ", ".join(maj))
            else:
                cx.execute("UPDATE prospects SET maj_le=? WHERE id=?", (t, pid))

        for valeur, genre in identifiants:
            cx.execute("INSERT OR IGNORE INTO identifiants (valeur, prospect_id, genre) VALUES (?,?,?)",
                       (valeur, pid, genre))
        cx.execute(
            "INSERT INTO interactions (prospect_id, canal, sens, texte, cle_unique, cree_le) VALUES (?,?,?,?,?,?)",
            (pid, canal, "entrant", texte, cle_message, t),
        )

        p = ligne(cx.execute("SELECT * FROM prospects WHERE id=?", (pid,)).fetchone())
        if nouveau:
            nb_alertes += _alertes(cx, config, "nouveau_prospect", p, texte)
        if info.get("appel_demande") and not p["appel_demande"]:
            cx.execute("UPDATE prospects SET appel_demande=1, statut='appel_demande', maj_le=? WHERE id=?", (t, pid))
            p["appel_demande"] = 1
            nb_alertes += _alertes(cx, config, "appel_demande", p, texte)
        cx.execute("COMMIT")
    except Exception:
        cx.execute("ROLLBACK")
        raise
    return {"resultat": "nouveau_prospect" if nouveau else "fiche_enrichie", "prospect_id": pid,
            "alertes": nb_alertes, "appel_demande": bool(info.get("appel_demande"))}


def _alertes(cx, config, type_alerte, p, dernier_message):
    tag = "[TEST - prospect fictif] " if p["fictif"] else ""
    if type_alerte == "appel_demande":
        titre = f"{tag}APPEL DEMANDÉ – {p['nom'] or 'prospect sans nom'}"
    else:
        titre = f"{tag}Nouvelle demande – {p['nom'] or 'prospect sans nom'} ({p['source']})"
    extrait = (dernier_message or "").strip().replace("\n", " ")
    if len(extrait) > 280:
        extrait = extrait[:277] + "…"
    corps = "\n".join([
        titre,
        f"Fiche : {p['id']}",
        f"Source : {p['source']} | Langue : {p['langue'] or '?'} | Pays : {p['pays'] or '?'}",
        f"Budget : {p['budget'] or 'non précisé'} | Zone : {p['zone'] or 'non précisée'} | Projet : {p['projet'] or 'non précisé'}",
        f"Message : « {extrait} »",
        "Action : rappeler dès que possible." if type_alerte == "appel_demande"
        else "Action : qualification en cours ; rien n'a été envoyé au prospect.",
    ])
    n = 0
    n += alertes.preparer(cx, type=type_alerte, canal="telegram", cle=f"{type_alerte}:{p['id']}:telegram",
                          corps=corps, prospect_id=p["id"])
    n += alertes.preparer(cx, type=type_alerte, canal="email", cle=f"{type_alerte}:{p['id']}:email",
                          corps=corps, sujet=titre, destinataire=config.email_alertes, prospect_id=p["id"])
    return n
