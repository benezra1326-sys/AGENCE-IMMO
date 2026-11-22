"""Bot Telegram des Applications, distinct du bot Immobilier.

Son propre jeton (APPS_TELEGRAM_BOT_TOKEN), son propre décalage de lecture : les informations des apps
ne passent jamais par le bot Immobilier, et inversement. Réservé au même compte (APPS_TELEGRAM_CHAT_ID,
ou à défaut TELEGRAM_CHAT_ID).
"""
from . import apps, pilotage
from .db import ecrire_reglage, journaliser, reglage

AIDE = """Commandes :
/apps – tous les projets d'apps et leur avancement
/app kapara – le détail d'une app
/taches – tâches des agents Apps
/blocages – ce qui bloque
/recap – récapitulatif Apps maintenant
Tout autre message est enregistré comme consigne pour la cheffe de projet Apps."""

CLE_OFFSET = "telegram_apps_offset"


class BotApps:
    def __init__(self, cx, config, api):
        self.cx, self.config, self.api = cx, config, api

    def dire(self, chat_id, texte):
        self.api.appel("sendMessage", {"chat_id": chat_id, "text": texte[:4000], "disable_web_page_preview": True})

    def relever(self):
        decalage = int(reglage(self.cx, CLE_OFFSET, "0"))
        maj = self.api.appel("getUpdates", {"offset": decalage, "timeout": 25, "allowed_updates": ["message"]}) or []
        for u in maj:
            try:
                self.traiter(u)
            finally:
                ecrire_reglage(self.cx, CLE_OFFSET, str(u["update_id"] + 1))
        return len(maj)

    def traiter(self, u):
        m = u.get("message")
        if not m or "text" not in m:
            return
        chat_id, texte = m["chat"]["id"], m["text"].strip()
        proprio = self.config.apps_telegram_proprietaire
        if not proprio or str(m.get("from", {}).get("id")) != str(proprio):
            journaliser(self.cx, "telegram apps", "accès refusé", str(m.get("from", {}).get("id")), None, niveau="erreur")
            if texte.startswith("/start") and not proprio:
                self.dire(chat_id, f"Ton identifiant Telegram est {m['from']['id']}. "
                                   "Ajoute-le comme APPS_TELEGRAM_CHAT_ID sur le serveur pour réserver ce bot à ton compte.")
            return
        journaliser(self.cx, "telegram apps", "message reçu d'Avishay", None, texte[:200])
        commande, _, reste = texte.partition(" ")
        commande = commande.split("@")[0].lower()
        f = {
            "/start": lambda: "Bot du back-office Avishay – Applications.\n\n" + AIDE,
            "/aide": lambda: AIDE, "/help": lambda: AIDE,
            "/apps": self.liste,
            "/app": lambda: self.detail(reste),
            "/taches": self.taches,
            "/blocages": self.blocages,
            "/recap": lambda: apps.recap(self.cx, self.config),
        }.get(commande)
        if f:
            return self.dire(chat_id, f())
        if texte.startswith("/"):
            return self.dire(chat_id, "Commande inconnue.\n\n" + AIDE)
        _, rep = pilotage.consigne(self.cx, texte, "telegram apps", message_id=m.get("message_id"),
                                   agent="apps-coordination")
        self.dire(chat_id, rep)

    def liste(self):
        l = apps.lister(self.cx)
        if not l:
            return "Aucune app suivie pour l'instant."
        return "\n".join(f"• {a['nom']} : {apps.NOMS_ETAPES[a['etape']]}, {a['avancement']} %, "
                         f"{apps.NOMS_STATUTS[a['statut']]}" + (" ⚠" if a["blocages"] else "") for a in l)

    def detail(self, nom):
        if not nom.strip():
            return "Format : /app kapara"
        a = apps.trouver(self.cx, nom)
        return apps.texte_app(a) if a else f"App « {nom.strip()} » introuvable. Tape /apps pour la liste."

    def taches(self):
        rows = self.cx.execute("SELECT id, titre, agent, statut FROM taches WHERE activite='apps' AND statut != 'terminee' "
                               "ORDER BY maj_le DESC LIMIT 15").fetchall()
        return "\n".join(f"• {r['id']} [{r['statut']}] {r['titre']} ({r['agent']})" for r in rows) or "Aucune tâche Apps ouverte."

    def blocages(self):
        l = [f"• {a['nom']} : {b}" for a in apps.lister(self.cx) for b in a["blocages"]]
        l += [f"• {r['titre']} : {r['raison_echec'] or 'raison non précisée'}" for r in self.cx.execute(
            "SELECT titre, raison_echec FROM taches WHERE activite='apps' AND statut IN ('bloquee','echec')").fetchall()]
        return "\n".join(l) or "Aucun blocage côté Apps."
