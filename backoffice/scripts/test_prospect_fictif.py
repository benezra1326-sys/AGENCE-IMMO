"""Parcours complet avec un prospect fictif, sans aucun envoi réel.

Usage (depuis le dossier backoffice) :
    python -m scripts.test_prospect_fictif [--depot CHEMIN] [--rapport FICHIER.md] [--apercu FICHIER.html]

Étapes : import des tâches du dépôt, première demande (formulaire), message rejoué, deuxième échange
(email écrit autrement), demande d'appel (WhatsApp), relance de la demande d'appel, commandes Telegram
via un faux Telegram, récap du matin. Vérifie : une seule fiche, historique complet, pas d'alerte en double,
alertes Telegram + email préparées et non envoyées.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app import alertes, leads, recap, taches
from app.config import Config
from app.db import connexion
from app.registre import masquer_biens, etat_complet, synchroniser_depot
from app.service import executeurs, programmer_recap
from app.telegram_bot import Bot


class FauxTelegram:
    def __init__(self):
        self.envoyes = []

    def appel(self, methode, params):
        if methode == "sendMessage":
            self.envoyes.append(params["text"])
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depot", default=None)
    ap.add_argument("--rapport", default=None)
    ap.add_argument("--apercu", default=None)
    ap.add_argument("--apercus", default=None, help="JSON {id_contenu: {medias: [{type, url, libelle, poster}]}} (médias déjà publiés)")
    a = ap.parse_args()

    c = Config()
    c.mode_envoi = "test"
    c.telegram_proprietaire = "1"  # identifiant factice pour le faux Telegram
    if a.depot:
        c.racine_depot = Path(a.depot)
    cx = connexion(":memory:")
    controles = []

    def verifier(nom, ok):
        controles.append((nom, bool(ok)))

    n = synchroniser_depot(cx, c.racine_depot)
    verifier(f"{n} tâches du dépôt importées, réimport sans doublon",
             synchroniser_depot(cx, c.racine_depot) == n and cx.execute("SELECT COUNT(*) FROM taches").fetchone()[0] == n)

    etapes = [
        dict(canal="formulaire", message_id="F-0001", nom="Camille Fictive", email="Camille.Fictive@example.com",
             langue="fr", pays="FR", fictif=True,
             texte="Bonjour, nous cherchons une résidence secondaire à Nueva Andalucía, budget 2,5 M€, plutôt une villa avec vue golf."),
        dict(canal="formulaire", message_id="F-0001", texte="(même formulaire reçu deux fois)"),
        dict(canal="email", message_id="E-0001", email="  camille.fictive@EXAMPLE.com ", telephone="+33 6 00 00 00 01",
             texte="Nous pourrions venir sur place fin janvier. Est-ce que la villa AB-0001 est encore disponible ?"),
        dict(canal="whatsapp", message_id="W-0001", telephone="0033600000001",
             texte="Bonjour, pouvez-vous m'appeler demain vers 10 h ?"),
        dict(canal="whatsapp", message_id="W-0002", telephone="+33600000001",
             texte="Merci de m'appeler quand vous pouvez."),
    ]
    resultats = [leads.recevoir(cx, c, **e) for e in etapes]
    attendus = ["nouveau_prospect", "doublon_message", "fiche_enrichie", "fiche_enrichie", "fiche_enrichie"]
    verifier("Résultats attendus à chaque message", [r["resultat"] for r in resultats] == attendus)
    verifier("Une seule fiche prospect", cx.execute("SELECT COUNT(*) FROM prospects").fetchone()[0] == 1)
    verifier("Historique : 4 messages (le doublon est ignoré)", cx.execute("SELECT COUNT(*) FROM interactions").fetchone()[0] == 4)
    verifier("Alertes de nouvelle demande : 1 Telegram + 1 email", resultats[0]["alertes"] == 2)
    verifier("Pas de nouvelle alerte pour les échanges suivants", resultats[2]["alertes"] == 0)
    verifier("Demande d'appel remontée tout de suite (Telegram + email)", resultats[3]["alertes"] == 2)
    verifier("Deuxième demande d'appel : pas d'alerte en double", resultats[4]["alertes"] == 0)
    verifier("Email adressé à avi@levygoldman.com",
             {r[0] for r in cx.execute("SELECT destinataire FROM alertes WHERE canal='email'")} == {"avi@levygoldman.com"})
    verifier("Mode test : rien n'est envoyé", alertes.expedier(cx, c)["envoyees"] == 0
             and cx.execute("SELECT COUNT(*) FROM alertes WHERE statut!='preparee'").fetchone()[0] == 0)

    api = FauxTelegram()
    bot = Bot(cx, c, api)
    for i, texte in enumerate(["/etat", "/prospects", "/taches"], start=1):
        bot.traiter({"update_id": i, "message": {"message_id": i, "from": {"id": 1}, "chat": {"id": 1}, "text": texte}})
    bot.traiter({"update_id": 9, "message": {"message_id": 9, "from": {"id": 42}, "chat": {"id": 42}, "text": "/etat"}})
    verifier("Telegram : 3 réponses à Avishay, compte inconnu ignoré", len(api.envoyes) == 3)
    verifier("Telegram : le prospect fictif apparaît dans /prospects", "Camille Fictive [fictif]" in api.envoyes[1])

    programmer_recap(cx, c, datetime.now(timezone.utc).replace(hour=9))
    taches.executer_en_attente(cx, executeurs(c))
    verifier("Récap du matin préparé (Telegram + email)", cx.execute("SELECT COUNT(*) FROM alertes WHERE type='recap'").fetchone()[0] == 2)

    p = cx.execute("SELECT * FROM prospects").fetchone()
    ok = all(v for _, v in controles)
    lignes = [
        "# Test du parcours prospect fictif",
        "",
        f"Exécuté le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC, en mode test (aucun envoi, aucune donnée réelle).",
        "",
        f"Résultat : **{'réussi' if ok else 'ÉCHEC'}** ({sum(v for _, v in controles)}/{len(controles)} contrôles).",
        "",
        "| Contrôle | Résultat |", "| --- | --- |",
        *[f"| {nom} | {'OK' if v else 'ÉCHEC'} |" for nom, v in controles],
        "",
        "## Fiche obtenue",
        "",
        f"- {p['id']} – {p['nom']} [fictif] – source {p['source']}, {p['pays']}, langue {p['langue']}",
        f"- Budget {p['budget']}, zone {p['zone']}, projet {p['projet']}, statut {p['statut']}",
        "",
        "## Alertes préparées (non envoyées)",
        "",
    ]
    for r in cx.execute("SELECT type, canal, destinataire, corps FROM alertes WHERE type!='recap' ORDER BY id"):
        lignes += [f"### {r['type']} – {r['canal']}" + (f" → {r['destinataire']}" if r["destinataire"] else ""), "", "```", r["corps"], "```", ""]
    lignes += ["## Récap du matin généré", "", "```", recap.generer(cx, c), "```", ""]
    rapport = "\n".join(lignes)
    if a.rapport:
        Path(a.rapport).parent.mkdir(parents=True, exist_ok=True)
        Path(a.rapport).write_text(rapport, encoding="utf-8")
    else:
        print(rapport)

    if a.apercu:
        etat = etat_complet(cx, c)

        def sans_chemins(v):  # l'aperçu figé n'ouvre aucun fichier : on n'y laisse que les libellés masqués
            if isinstance(v, dict):
                return v.get("libelle") if set(v) == {"chemin", "libelle"} else {k: sans_chemins(x) for k, x in v.items()}
            return [sans_chemins(x) for x in v] if isinstance(v, list) else v
        medias = json.loads(Path(a.apercus).read_text(encoding="utf-8")) if a.apercus else {}
        for ct in etat["contenus"]:
            textes = []
            dossier = next((Path(c.racine_depot) / Path(f).parent for f in ((x.get("chemin") if isinstance(x, dict) else x) for x in (ct.get("fichiers") or []))
                            if isinstance(f, str) and f.startswith("contenus/")), None)
            for md in sorted(dossier.glob("*.md")) if dossier and dossier.exists() else []:
                titre = {"legende-et-note.md": "Légende et note interne", "textes-v2.md": "Textes, légende et script voix off",
                         "brouillon-textes.md": "Textes et légende"}.get(md.name, md.stem.replace("-", " "))
                textes.append({"titre": titre, "texte": md.read_text(encoding="utf-8")})
            m = (medias.get(ct["id"]) or {}).get("medias", [])
            if m or textes:
                ct["apercu"] = {"medias": m, "textes": textes}
        for t in etat["taches"]:  # rapports lisibles directement dans l'aperçu
            for f in t.get("fichiers") or []:
                ch = f.get("chemin") if isinstance(f, dict) else f
                if isinstance(ch, str) and ch.startswith("ops/rapports/") and ch.endswith(".md") and (Path(c.racine_depot) / ch).exists():
                    t.setdefault("textes", []).append({"titre": "Lire le rapport", "texte": (Path(c.racine_depot) / ch).read_text(encoding="utf-8")})
        etat = masquer_biens(etat, c.racine_depot)
        etat = sans_chemins(etat)
        source = (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(encoding="utf-8")
        donnees = json.dumps(etat, ensure_ascii=False).replace("</", "<\\/")
        Path(a.apercu).write_text(source.replace("<script>\n(function", f"<script>window.__ETAT__ = {donnees};</script>\n<script>\n(function", 1),
                                  encoding="utf-8")
    print("\n".join(f"{'OK ' if v else 'KO '} {nom}" for nom, v in controles), file=sys.stderr)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
