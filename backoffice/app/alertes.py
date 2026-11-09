"""Préparation et envoi des alertes (Telegram et email).

En mode "test" (par défaut), les alertes sont préparées et enregistrées mais jamais envoyées.
Chaque alerte a une clé unique : la même alerte n'est jamais préparée deux fois.
"""
import json
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage

from .db import journaliser, maintenant

MAX_TENTATIVES_ENVOI = 5


def preparer(cx, *, type, canal, cle, corps, sujet=None, destinataire=None, prospect_id=None):
    cur = cx.execute(
        """INSERT OR IGNORE INTO alertes (type, canal, cle_unique, destinataire, sujet, corps, statut,
                                          prospect_id, cree_le)
           VALUES (?,?,?,?,?,?, 'preparee', ?, ?)""",
        (type, canal, cle, destinataire, sujet, corps, prospect_id, maintenant()),
    )
    if cur.rowcount:
        journaliser(cx, "alertes", f"alerte {canal} préparée", prospect_id, type)
    return cur.rowcount == 1


class TelegramEnvoi:
    def __init__(self, token, chat_id):
        self.token, self.chat_id = token, chat_id

    def envoyer(self, texte, boutons=None):
        params = {"chat_id": self.chat_id, "text": texte, "disable_web_page_preview": True}
        if boutons:
            params["reply_markup"] = {"inline_keyboard": boutons}
        appel_telegram(self.token, "sendMessage", params)


def appel_telegram(token, methode, params, timeout=35):
    url = f"https://api.telegram.org/bot{token}/{methode}"
    req = urllib.request.Request(url, data=json.dumps(params).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as rep:  # noqa: S310 - URL fixe Telegram
        donnees = json.loads(rep.read().decode("utf-8"))
    if not donnees.get("ok"):
        # Ne jamais inclure le token dans l'erreur
        raise RuntimeError(f"Telegram {methode} refusé : {donnees.get('description', 'inconnu')}")
    return donnees.get("result")


class EmailEnvoi:
    def __init__(self, config):
        self.c = config

    def envoyer(self, destinataire, sujet, corps):
        msg = EmailMessage()
        msg["From"] = self.c.smtp_expediteur
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg.set_content(corps)
        with smtplib.SMTP_SSL(self.c.smtp_hote, self.c.smtp_port, context=ssl.create_default_context(), timeout=30) as s:
            s.login(self.c.smtp_utilisateur, self.c.smtp_mot_de_passe)
            s.send_message(msg)


def expedier(cx, config, telegram=None, email=None):
    """Envoie les alertes préparées si le mode réel est actif et la connexion configurée."""
    if config.mode_envoi != "reel":
        return {"envoyees": 0, "raison": "mode test : alertes préparées, aucun envoi"}
    envoyees = 0
    rows = cx.execute(
        "SELECT * FROM alertes WHERE statut IN ('preparee','echec') AND tentatives < ? ORDER BY id",
        (MAX_TENTATIVES_ENVOI,),
    ).fetchall()
    for a in rows:
        try:
            if a["canal"] == "telegram":
                if telegram is None:
                    raise RuntimeError("bot Telegram non configuré")
                telegram.envoyer(a["corps"])
            else:
                if email is None:
                    raise RuntimeError("envoi email non configuré")
                email.envoyer(a["destinataire"], a["sujet"], a["corps"])
            cx.execute("UPDATE alertes SET statut='envoyee', envoyee_le=?, erreur=NULL, tentatives=tentatives+1 WHERE id=?",
                       (maintenant(), a["id"]))
            envoyees += 1
        except Exception as e:  # noqa: BLE001
            cx.execute("UPDATE alertes SET statut='echec', erreur=?, tentatives=tentatives+1 WHERE id=?",
                       (f"{type(e).__name__}: {e}"[:300], a["id"]))
            journaliser(cx, "alertes", f"échec d'envoi {a['canal']}", a["prospect_id"], str(e)[:300], niveau="erreur")
    return {"envoyees": envoyees}
