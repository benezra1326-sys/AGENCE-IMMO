"""Récapitulatif du matin, en français."""
from datetime import datetime, timedelta, timezone

from .config import FUSEAU
from .registre import charger_registre

NOMS_STATUTS = {"en_attente": "en attente", "en_cours": "en cours", "terminee": "terminées",
                "echec": "en échec", "bloquee": "bloquées"}


def generer(cx, config, maintenant_dt=None):
    now = maintenant_dt or datetime.now(timezone.utc)
    depuis = (now - timedelta(days=1)).isoformat()
    un = lambda q, *p: cx.execute(q, p).fetchone()[0] or 0  # noqa: E731
    date_locale = now.astimezone(FUSEAU).strftime("%d/%m/%Y")
    l = [f"Récap du {date_locale}"]
    if config.mode_envoi != "reel":
        l.append("(mode test : aucune alerte n'est réellement envoyée)")

    prod = cx.execute("SELECT titre, agent FROM taches WHERE statut='terminee' AND maj_le >= ? ORDER BY maj_le", (depuis,)).fetchall()
    l.append(f"\nProductions (24 h) : {len(prod)}")
    l += [f"• {r['titre']} ({r['agent']})" for r in prod[:8]]

    av = cx.execute("SELECT id, titre FROM contenus WHERE statut='a_valider'").fetchall()
    l.append(f"\nÀ valider : {len(av)}")
    l += [f"• {r['id']} – {r['titre']}" for r in av[:8]]
    l.append(f"Publications : {un('SELECT COUNT(*) FROM contenus WHERE statut=? AND maj_le >= ?', 'publie', depuis)} "
             "(publication automatique non activée)")

    l.append(f"\nConversations (24 h) : {un('SELECT COUNT(*) FROM interactions WHERE cree_le >= ?', depuis)} messages")
    nouveaux = cx.execute("SELECT id, nom, budget, appel_demande, fictif FROM prospects WHERE cree_le >= ?", (depuis,)).fetchall()
    l.append(f"Prospects nouveaux : {len(nouveaux)}")
    for p in nouveaux[:8]:
        tag = " [fictif]" if p["fictif"] else ""
        appel = " – APPEL DEMANDÉ" if p["appel_demande"] else ""
        l.append(f"• {p['nom'] or p['id']}{tag}, budget {p['budget'] or '?'}{appel}")

    partenaires = charger_registre()["partenaires"]
    l.append(f"\nProspection B2B : {len(partenaires)} partenaires en liste, 0 contacté (envoi LinkedIn manuel par toi)")

    l.append("\nTâches :")
    stats = {r["statut"]: r["n"] for r in cx.execute("SELECT statut, COUNT(*) n FROM taches GROUP BY statut")}
    l.append(", ".join(f"{stats.get(s, 0)} {n}" for s, n in NOMS_STATUTS.items()))

    bloq = cx.execute("SELECT id, titre, raison_echec FROM taches WHERE statut IN ('bloquee','echec') ORDER BY maj_le DESC").fetchall()
    manquantes = [c["nom"] for c in charger_registre()["connexions"].get("connexions", []) if c["statut"] == "manquant"]
    l.append("\nBlocages :")
    l += [f"• {r['titre']} : {r['raison_echec'] or 'raison non précisée'}" for r in bloq[:6]]
    if manquantes:
        l.append(f"• Connexions manquantes : {', '.join(manquantes[:6])}")

    cout_jour = un("SELECT SUM(montant_eur) FROM couts WHERE quand >= ?", depuis)
    l.append(f"\nCoûts (24 h) : {cout_jour:.2f} €")
    l.append("Pubs : non activées")
    return "\n".join(l)
