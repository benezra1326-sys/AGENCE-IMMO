"""Envoie un lot validé (lot.json) aux agents via l'API WhatsApp Cloud de Meta.

Garde-fous :
  - par défaut, SIMULATION : affiche ce qui partirait, n'envoie rien ;
  - envoi réel seulement avec --confirme ET un lot au statut « valide » (posé par le back-office
    ou par Telegram quand Avishay a dit OK) ;
  - seuls les agents présents dans le lot (donc avec « Accord WhatsApp = oui ») sont contactés ;
  - le message est un modèle approuvé par Meta (obligatoire pour écrire en premier).

Variables d'environnement (Project settings > Environment, jamais dans le chat) :
  WHATSAPP_TOKEN            jeton d'accès permanent (utilisateur système Meta)
  WHATSAPP_PHONE_NUMBER_ID  identifiant du numéro WhatsApp Business
  WHATSAPP_TEMPLATE         nom du modèle approuvé (défaut : nouveau_bien_agents)
  WHATSAPP_API_VERSION      défaut : v23.0

Modèle à faire approuver dans WhatsApp Manager (une version par langue fr / en / es) :
  en-tête : Document ; corps avec 4 variables {{1}} prénom, {{2}} type, {{3}} zone, {{4}} prix.

Usage : python3 envoyer_whatsapp.py <lot.json> [--confirme]
"""
import argparse
import json
import os
import sys
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

LANGUES = {"FR": "fr", "EN": "en", "ES": "es"}


def appel(url, token, data=None, fichier=None):
    if fichier:
        bord = uuid.uuid4().hex
        corps = b""
        for k, v in {"messaging_product": "whatsapp", "type": "application/pdf"}.items():
            corps += f"--{bord}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        corps += (f"--{bord}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{Path(fichier).name}\"\r\n"
                  "Content-Type: application/pdf\r\n\r\n").encode() + Path(fichier).read_bytes() + f"\r\n--{bord}--\r\n".encode()
        req = urllib.request.Request(url, corps, {"Authorization": f"Bearer {token}",
                                                  "Content-Type": f"multipart/form-data; boundary={bord}"})
    else:
        req = urllib.request.Request(url, json.dumps(data).encode(), {"Authorization": f"Bearer {token}",
                                                                       "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lot")
    ap.add_argument("--confirme", action="store_true", help="envoi réel (sinon simulation)")
    a = ap.parse_args()
    chemin = Path(a.lot)
    lot = json.loads(chemin.read_text(encoding="utf-8"))

    print(f"Lot {lot['id']} ({lot['ref']}) : statut {lot['statut']}, {len(lot['envois'])} destinataire(s)")
    for e in lot["envois"]:
        print(f"  -> {e['agent']} ({e['agence']}) {e['whatsapp']} [{e['langue']}]")
    if not a.confirme:
        print("SIMULATION : rien n'a été envoyé. Ajoutez --confirme après le OK d'Avishay.")
        return
    if lot["statut"] != "valide":
        sys.exit("Refusé : le lot n'est pas validé par Avishay (statut attendu : valide).")
    token, numero = os.environ.get("WHATSAPP_TOKEN"), os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not numero:
        sys.exit("WHATSAPP_TOKEN ou WHATSAPP_PHONE_NUMBER_ID manquant (Project settings > Environment).")
    base = f"https://graph.facebook.com/{os.environ.get('WHATSAPP_API_VERSION', 'v23.0')}/{numero}"
    modele = os.environ.get("WHATSAPP_TEMPLATE", "nouveau_bien_agents")

    media_id = appel(f"{base}/media", token, fichier=lot["fiche_pdf"])["id"]
    for e in lot["envois"]:
        if e.get("envoye_le"):
            continue
        p = e["parametres"]
        corps = {
            "messaging_product": "whatsapp", "to": e["whatsapp"].lstrip("+"), "type": "template",
            "template": {"name": modele, "language": {"code": LANGUES[e["langue"]]}, "components": [
                {"type": "header", "parameters": [{"type": "document", "document": {
                    "id": media_id, "filename": Path(lot["fiche_pdf"]).name}}]},
                {"type": "body", "parameters": [{"type": "text", "text": str(p[k])} for k in ("prenom", "type", "zone", "prix")]},
            ]},
        }
        try:
            r = appel(f"{base}/messages", token, corps)
            e["envoye_le"], e["message_id"] = datetime.now().isoformat(timespec="seconds"), r["messages"][0]["id"]
            print(f"  envoyé à {e['agent']}")
        except Exception as err:  # on note et on continue, rien n'est renvoyé deux fois
            e["erreur"] = str(err)
            print(f"  ÉCHEC {e['agent']} : {err}")
    lot["statut"] = "envoye" if all(e.get("envoye_le") for e in lot["envois"]) else "partiel"
    chemin.write_text(json.dumps(lot, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
