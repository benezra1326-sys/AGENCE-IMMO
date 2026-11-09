"""Configuration du back-office, lue uniquement dans les variables d'environnement.

Aucun secret n'est écrit dans le code ni dans le dépôt : voir deploy/.env.exemple.
"""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

RACINE_BACKOFFICE = Path(__file__).resolve().parent.parent
RACINE_DEPOT = RACINE_BACKOFFICE.parent

FUSEAU = ZoneInfo("Europe/Madrid")


def _env(nom, defaut=None):
    valeur = os.environ.get(nom)
    return valeur if valeur not in (None, "") else defaut


class Config:
    def __init__(self):
        self.chemin_base = Path(_env("BO_BASE", str(RACINE_BACKOFFICE / "donnees" / "backoffice.sqlite3")))
        self.racine_depot = Path(_env("BO_DEPOT", str(RACINE_DEPOT)))
        # "test" : les alertes sont préparées et enregistrées, jamais envoyées.
        # "reel" : envoi effectif (à activer seulement après l'accord d'Avishay).
        self.mode_envoi = _env("BO_MODE_ENVOI", "test")
        self.email_alertes = _env("BO_EMAIL_ALERTES", "avi@levygoldman.com")
        self.telegram_token = _env("TELEGRAM_BOT_TOKEN")
        self.telegram_proprietaire = _env("TELEGRAM_OWNER_ID")  # identifiant numérique du compte d'Avishay
        self.smtp_hote = _env("SMTP_HOST")
        self.smtp_port = int(_env("SMTP_PORT", "465"))
        self.smtp_utilisateur = _env("SMTP_USER")
        self.smtp_mot_de_passe = _env("SMTP_PASSWORD")
        self.smtp_expediteur = _env("SMTP_FROM", self.smtp_utilisateur)
        self.dashboard_hote = _env("BO_HOST", "127.0.0.1")
        self.dashboard_port = int(_env("BO_PORT", "8787"))
        self.dashboard_mot_de_passe = _env("BO_DASHBOARD_PASSWORD")
        self.heure_recap = _env("BO_HEURE_RECAP", "08:00")
        self.jeton_demandes = _env("BO_INTAKE_TOKEN")  # jeton des formulaires / webhooks entrants
        self.anthropic_cle_presente = bool(_env("ANTHROPIC_API_KEY"))

    @property
    def telegram_configure(self):
        return bool(self.telegram_token and self.telegram_proprietaire)

    @property
    def email_configure(self):
        return bool(self.smtp_hote and self.smtp_utilisateur and self.smtp_mot_de_passe)
