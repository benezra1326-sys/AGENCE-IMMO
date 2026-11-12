"""Tableau de bord privé (HTTP) + API JSON. Bibliothèque standard Python uniquement.

Sécurité : mot de passe obligatoire dès que le service écoute ailleurs qu'en local.
À placer derrière HTTPS (Caddy) en production.
"""
import base64
import hmac
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import leads, pilotage, taches
from .config import RACINE_BACKOFFICE
from .registre import etat_complet

STATIQUE = RACINE_BACKOFFICE / "static"
DOSSIERS_FICHIERS = ("ops", "data", "livrables", "contenus")  # fichiers consultables depuis le tableau de bord
VERROU = threading.Lock()


def fabrique(cx, config):
    class Gestionnaire(BaseHTTPRequestHandler):
        server_version = "backoffice"

        def log_message(self, *args):  # pas de journal d'accès (évite d'écrire des en-têtes sensibles)
            return

        def _auth(self):
            if not config.dashboard_mot_de_passe:
                return config.dashboard_hote in ("127.0.0.1", "localhost")
            entete = self.headers.get("Authorization", "")
            if entete.startswith("Basic "):
                try:
                    _, _, mdp = base64.b64decode(entete[6:]).decode("utf-8").partition(":")
                except ValueError:
                    mdp = ""
                if hmac.compare_digest(mdp, config.dashboard_mot_de_passe):
                    return True
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Back-office", charset="UTF-8"')
            self.end_headers()
            return False

        def _json(self, code, obj):
            corps = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)

        def _corps(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 100_000:
                return {}
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                return {}

        def do_GET(self):  # noqa: N802
            chemin = urlparse(self.path).path
            if chemin == "/sante":
                return self._json(200, {"ok": True})
            if not self._auth():
                return
            if chemin in ("/", "/index.html"):
                entete = (b'<!doctype html><html lang="fr"><meta charset="utf-8">'
                          b'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">')
                return self._fichier(STATIQUE / "index.html", prefixe=entete)
            if chemin == "/api/etat":
                with VERROU:
                    return self._json(200, etat_complet(cx, config))
            if chemin.startswith("/fichiers/"):
                rel = Path(unquote(chemin[len("/fichiers/"):]))
                base = Path(config.racine_depot).resolve()
                cible = (base / rel).resolve()
                autorises = [(base / d).resolve() for d in DOSSIERS_FICHIERS]
                if any(a in cible.parents for a in autorises) and cible.is_file():
                    return self._fichier(cible)
            self._json(404, {"erreur": "introuvable"})

        def do_POST(self):  # noqa: N802
            chemin = urlparse(self.path).path
            if chemin == "/api/demandes":
                return self._demande_entrante()
            if not self._auth():
                return
            d = self._corps()
            morceaux = chemin.strip("/").split("/")
            with VERROU:
                if morceaux[:2] == ["api", "contenus"] and len(morceaux) == 4:
                    cid, action = morceaux[2], morceaux[3]
                    if action == "valider":
                        ok, msg = pilotage.valider_contenu(cx, cid, "tableau de bord")
                    elif action == "modifier":
                        ok, msg = pilotage.demander_modification(cx, cid, d.get("texte", ""), "tableau de bord")
                    else:
                        return self._json(404, {"erreur": "action inconnue"})
                    return self._json(200 if ok else 400, {"ok": ok, "message": msg})
                if morceaux[:2] == ["api", "taches"] and len(morceaux) == 4 and morceaux[3] == "reprendre":
                    ok = taches.reprendre(cx, morceaux[2])
                    return self._json(200 if ok else 400, {"ok": ok, "message": "Tâche relancée." if ok else "Rien à reprendre."})
                if chemin == "/api/consigne":
                    t, msg = pilotage.consigne(cx, d.get("texte", ""), "tableau de bord", agent=d.get("agent"))
                    return self._json(200 if t else 400, {"ok": bool(t), "message": msg})
            self._json(404, {"erreur": "introuvable"})

        def _demande_entrante(self):
            """Point d'entrée des formulaires / webhooks (site, Meta Lead Ads). Protégé par un jeton dédié."""
            jeton = getattr(config, "jeton_demandes", None)
            if not jeton or not hmac.compare_digest(self.headers.get("X-Jeton", ""), jeton):
                return self._json(401, {"erreur": "jeton invalide"})
            d = self._corps()
            if not d.get("message_id") or not d.get("canal"):
                return self._json(400, {"erreur": "canal et message_id requis"})
            with VERROU:
                r = leads.recevoir(cx, config, canal=d["canal"], message_id=str(d["message_id"]), texte=d.get("texte", ""),
                                   nom=d.get("nom"), email=d.get("email"), telephone=d.get("telephone"),
                                   compte=d.get("compte"), langue=d.get("langue"), pays=d.get("pays"))
            self._json(200, r)

        def _fichier(self, chemin, prefixe=b""):
            data = prefixe + Path(chemin).read_bytes()
            self.send_response(200)
            type_mime = mimetypes.guess_type(str(chemin))[0] or "application/octet-stream"
            if type_mime.startswith("text/") or type_mime.endswith("json"):
                type_mime += "; charset=utf-8"
            self.send_header("Content-Type", type_mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

    return Gestionnaire


def lancer(cx, config):
    if not config.dashboard_mot_de_passe and config.dashboard_hote not in ("127.0.0.1", "localhost"):
        raise SystemExit("BO_DASHBOARD_PASSWORD est obligatoire quand le tableau de bord est accessible hors du serveur.")
    srv = ThreadingHTTPServer((config.dashboard_hote, config.dashboard_port), fabrique(cx, config))
    return srv
