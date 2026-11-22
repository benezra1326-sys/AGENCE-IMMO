"""Service principal : tourne en continu sur le serveur (Mac éteint).

Boucles :
- tableau de bord HTTP ;
- relève Telegram (si le bot est configuré) ;
- toutes les 60 s : exécution des tâches serveur dues (avec reprise), envoi des alertes préparées ;
- toutes les 5 min : synchronisation des tâches écrites dans le dépôt (git pull puis import) ;
- chaque jour à l'heure du récap (08:00 Madrid) : tâche « recap » unique par jour.

Lancement : python -m app.service   (depuis le dossier backoffice)
"""
import subprocess
import threading
import time
from datetime import datetime, timezone

from . import alertes, recap, taches
from .config import FUSEAU, Config
from .db import connexion, journaliser
from .registre import synchroniser_depot
from .serveur import VERROU, lancer
from .telegram_bot import Bot, TelegramAPI


def executeurs(config):
    def tache_recap(cx, t):
        texte = recap.generer(cx, config)
        jour = t["donnees"].get("jour") if isinstance(t["donnees"], dict) else None
        alertes.preparer(cx, type="recap", canal="telegram", cle=f"recap:{jour}:telegram", corps=texte)
        alertes.preparer(cx, type="recap", canal="email", cle=f"recap:{jour}:email", corps=texte,
                         sujet=f"Récap du matin – {jour}", destinataire=config.email_alertes)
        return "Récap généré et préparé pour Telegram et email.", [], 0.0

    return {"recap": tache_recap}


def programmer_recap(cx, config, now=None):
    now = (now or datetime.now(timezone.utc)).astimezone(FUSEAU)
    if now.strftime("%H:%M") < config.heure_recap:
        return None
    jour = now.strftime("%Y-%m-%d")
    t, _ = taches.creer(cx, activite="immo", agent="coordination", titre=f"Récap du matin {jour}",
                        cle_unique=f"recap:{jour}", type="recap", source="planification quotidienne",
                        donnees={"jour": jour})
    return t


def git_pull(racine):
    try:
        subprocess.run(["git", "-C", str(racine), "pull", "--ff-only", "--quiet"], timeout=60, check=True,
                       capture_output=True)
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def boucle(cx, config, bot, arret):
    dernier_sync = 0.0
    tg = alertes.TelegramEnvoi(config.telegram_token, config.telegram_proprietaire) if config.telegram_configure else None
    em = alertes.EmailEnvoi(config) if config.email_configure else None
    while not arret.is_set():
        try:
            with VERROU:
                if time.time() - dernier_sync > 300:
                    git_pull(config.racine_depot)
                    synchroniser_depot(cx, config.racine_depot)
                    dernier_sync = time.time()
                programmer_recap(cx, config)
                taches.executer_en_attente(cx, executeurs(config))
                alertes.expedier(cx, config, telegram=tg, email=em)
        except Exception as e:  # noqa: BLE001 - le service ne doit jamais s'arrêter sur une erreur
            journaliser(cx, "service", "erreur de boucle", None, f"{type(e).__name__}: {e}"[:300], niveau="erreur")
        arret.wait(60)


def boucle_telegram(cx, bot, arret):
    while not arret.is_set():
        try:
            bot.relever()
        except Exception as e:  # noqa: BLE001
            with VERROU:
                journaliser(cx, "telegram", "erreur de relève", None, f"{type(e).__name__}"[:100], niveau="erreur")
            arret.wait(30)


def main():
    config = Config()
    cx = connexion(config.chemin_base)
    journaliser(cx, "service", "démarrage", None, f"mode {config.mode_envoi}")
    synchroniser_depot(cx, config.racine_depot)
    arret = threading.Event()
    bot = Bot(cx, config, TelegramAPI(config.telegram_token)) if config.telegram_configure else None
    threading.Thread(target=boucle, args=(cx, config, bot, arret), daemon=True).start()
    if bot:
        threading.Thread(target=boucle_telegram, args=(cx, bot, arret), daemon=True).start()
    srv = lancer(cx, config)
    print(f"Tableau de bord : http://{config.dashboard_hote}:{config.dashboard_port}  (mode {config.mode_envoi})")
    try:
        srv.serve_forever()
    finally:
        arret.set()


if __name__ == "__main__":
    main()
