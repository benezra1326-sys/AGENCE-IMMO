"""Bot Telegram réservé au compte d'Avishay.

Seul l'identifiant TELEGRAM_CHAT_ID est servi ; tout autre compte est ignoré (et noté dans le journal
sans recopier son message). Fonctionne en « long polling » : aucune adresse publique n'est nécessaire.
"""
from . import pilotage, recap
from .db import ecrire_reglage, journaliser, reglage
from .registre import charger_registre, etats_agents, nom_agent

AIDE = """Commandes :
/etat – état général des trois activités
/etat immo – détail Immobilier
/taches – tâches en cours, en attente, en échec
/avalider – contenus à valider (avec boutons)
/valider C-… – valider un contenu
/modifier C-… ta demande – demander une modification
/prospects – derniers prospects
/recap – récapitulatif maintenant
Tout autre message est enregistré comme consigne."""


class Bot:
    def __init__(self, cx, config, api):
        """api : objet avec .appel(methode, params) -> résultat (vrai Telegram ou faux pour les tests)."""
        self.cx, self.config, self.api = cx, config, api

    # --- envoi -------------------------------------------------------------------------------
    def dire(self, chat_id, texte, boutons=None):
        params = {"chat_id": chat_id, "text": texte[:4000], "disable_web_page_preview": True}
        if boutons:
            params["reply_markup"] = {"inline_keyboard": boutons}
        self.api.appel("sendMessage", params)

    # --- réception ---------------------------------------------------------------------------
    def relever(self):
        """Récupère les nouveaux messages. Le décalage est mémorisé : un message n'est jamais traité deux fois."""
        decalage = int(reglage(self.cx, "telegram_offset", "0"))
        maj = self.api.appel("getUpdates", {"offset": decalage, "timeout": 25,
                                             "allowed_updates": ["message", "callback_query"]}) or []
        for u in maj:
            try:
                self.traiter(u)
            finally:
                ecrire_reglage(self.cx, "telegram_offset", str(u["update_id"] + 1))
        return len(maj)

    def traiter(self, u):
        if "callback_query" in u:
            q = u["callback_query"]
            if not self._autorise(q.get("from", {})):
                return
            self.api.appel("answerCallbackQuery", {"callback_query_id": q["id"]})
            return self._bouton(q["message"]["chat"]["id"], q.get("data", ""))
        m = u.get("message")
        if not m or "text" not in m:
            return
        chat_id, texte = m["chat"]["id"], m["text"].strip()
        if not self._autorise(m.get("from", {})):
            if texte.startswith("/start") and not self.config.telegram_proprietaire:
                # Mise en service : donne l'identifiant à recopier dans la configuration du serveur
                self.dire(chat_id, f"Ton identifiant Telegram est {m['from']['id']}. "
                                   "Ajoute-le comme TELEGRAM_CHAT_ID sur le serveur pour réserver ce bot à ton compte.")
            return
        journaliser(self.cx, "telegram", "message reçu d'Avishay", None, texte[:200])
        attente = reglage(self.cx, "telegram_modif_en_attente")
        if attente and not texte.startswith("/"):
            ecrire_reglage(self.cx, "telegram_modif_en_attente", "")
            return self.dire(chat_id, pilotage.demander_modification(self.cx, attente, texte, "telegram")[1])
        commande, _, reste = texte.partition(" ")
        commande = commande.split("@")[0].lower()
        f = {
            "/start": lambda: self.dire(chat_id, "Bot du back-office Avishay – Immobilier.\n\n" + AIDE),
            "/aide": lambda: self.dire(chat_id, AIDE), "/help": lambda: self.dire(chat_id, AIDE),
            "/etat": lambda: self.dire(chat_id, self.etat(reste.strip().lower())),
            "/taches": lambda: self.dire(chat_id, self.liste_taches()),
            "/avalider": lambda: self.a_valider(chat_id),
            "/valider": lambda: self.dire(chat_id, pilotage.valider_contenu(self.cx, reste.strip(), "telegram")[1]),
            "/modifier": lambda: self._modifier(chat_id, reste),
            "/prospects": lambda: self.dire(chat_id, self.prospects()),
            "/recap": lambda: self.dire(chat_id, recap.generer(self.cx, self.config)),
        }.get(commande)
        if f:
            return f()
        if texte.startswith("/"):
            return self.dire(chat_id, "Commande inconnue.\n\n" + AIDE)
        _, rep = pilotage.consigne(self.cx, texte, "telegram", message_id=m.get("message_id"))
        self.dire(chat_id, rep)

    def _autorise(self, expediteur):
        ok = bool(self.config.telegram_proprietaire) and str(expediteur.get("id")) == str(self.config.telegram_proprietaire)
        if not ok:
            journaliser(self.cx, "telegram", "accès refusé", str(expediteur.get("id")), None, niveau="erreur")
        return ok

    def _modifier(self, chat_id, reste):
        cid, _, demande = reste.strip().partition(" ")
        if not cid:
            return self.dire(chat_id, "Format : /modifier C-… ta demande")
        if not demande.strip():
            ecrire_reglage(self.cx, "telegram_modif_en_attente", cid)
            return self.dire(chat_id, f"Quelle modification pour {cid} ? Écris-la dans ton prochain message.")
        self.dire(chat_id, pilotage.demander_modification(self.cx, cid, demande, "telegram")[1])

    def _bouton(self, chat_id, data):
        action, _, cid = data.partition(":")
        if action == "val":
            return self.dire(chat_id, pilotage.valider_contenu(self.cx, cid, "telegram")[1])
        if action == "mod":
            ecrire_reglage(self.cx, "telegram_modif_en_attente", cid)
            return self.dire(chat_id, f"Quelle modification pour {cid} ? Écris-la dans ton prochain message.")

    # --- contenus des réponses -----------------------------------------------------------------
    def etat(self, cible=""):
        reg = charger_registre()
        acts = reg["activites"].get("activites", [])
        if cible in ("immo", "immobilier"):
            agents = etats_agents(self.cx, reg["agents"])
            lignes = ["Immobilier – agents :"]
            for a in agents:
                lignes.append(f"• {nom_agent(a['id'], agents)} : {a['etat']}")
            return "\n".join(lignes)
        lignes = ["État général :"]
        for a in acts:
            n = self.cx.execute("SELECT COUNT(*) FROM taches WHERE activite=? AND statut IN ('en_attente','en_cours')",
                                (a["id"],)).fetchone()[0]
            lignes.append(f"• {a['nom']} : {a['etat'].replace('_', ' ')} – {n} tâche(s) ouvertes")
        echecs = self.cx.execute("SELECT COUNT(*) FROM taches WHERE statut IN ('echec','bloquee')").fetchone()[0]
        lignes.append(f"Échecs ou blocages : {echecs}")
        return "\n".join(lignes)

    def liste_taches(self):
        rows = self.cx.execute(
            "SELECT id, titre, agent, statut, raison_echec FROM taches WHERE statut != 'terminee' ORDER BY maj_le DESC LIMIT 15").fetchall()
        if not rows:
            return "Aucune tâche ouverte."
        return "\n".join(f"• {r['id']} [{r['statut']}] {r['titre']} ({nom_agent(r['agent'])})"
                         + (f" – {r['raison_echec']}" if r["raison_echec"] else "") for r in rows)

    def a_valider(self, chat_id):
        cs = pilotage.contenus_a_valider(self.cx)
        if not cs:
            return self.dire(chat_id, "Aucun contenu à valider.")
        for c in cs[:10]:
            self.dire(chat_id, f"{c['id']} – {c['titre']} ({c['format'] or '?'}, {c['langue'] or '?'})",
                      boutons=[[{"text": "Valider", "callback_data": f"val:{c['id']}"},
                                {"text": "Demander une modification", "callback_data": f"mod:{c['id']}"}]])

    def prospects(self):
        rows = self.cx.execute("SELECT id, nom, source, budget, statut, fictif FROM prospects ORDER BY maj_le DESC LIMIT 10").fetchall()
        if not rows:
            return "Aucun prospect."
        return "\n".join(f"• {r['nom'] or r['id']}{' [fictif]' if r['fictif'] else ''} – {r['source']}, "
                         f"budget {r['budget'] or '?'}, {r['statut']}" for r in rows)


class TelegramAPI:
    """Accès réel à l'API Telegram (utilisé seulement si le jeton est configuré)."""

    def __init__(self, token):
        from .alertes import appel_telegram
        self._appel, self._token = appel_telegram, token

    def appel(self, methode, params):
        return self._appel(self._token, methode, params)
