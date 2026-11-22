import base64
import json
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from app import alertes, apps, recap
from app.db import connexion
from app.registre import charger_registre, etat_complet
from app.serveur import fabrique
from app.service import executeurs, programmer_recap
from app.telegram_apps import BotApps
from app.telegram_bot import Bot
from tests.test_backoffice import PROPRIO, FauxTelegram, config_test, msg

FICHE = {"id": "kapara", "nom": "KAPARA", "etape": "cadrage", "statut": "en_cours", "avancement": 10,
         "resume": "Squelette en cours.", "prochaine_etape": "Découper les chantiers.", "blocages": [],
         "chantiers": [{"nom": "Squelette", "statut": "en_cours", "avancement": 30, "responsable": "apps-dev"}],
         "liens": [{"libelle": "Dépôt", "url": "https://github.com/x/y"}, {"libelle": "mauvais", "url": "javascript:alert(1)"}],
         "maj_le": "2026-11-22T03:30:00Z"}


def alertes_apps(cx):
    return cx.execute("SELECT * FROM alertes WHERE canal='telegram_apps' ORDER BY id").fetchall()


class TestFiches(unittest.TestCase):
    def setUp(self):
        self.cx = connexion(":memory:")

    def test_validation(self):
        f = apps.valider(FICHE)
        self.assertEqual(len(f["liens"]), 1)  # lien non https écarté
        self.assertEqual(f["chantiers"][0]["avancement"], 30)
        for mauvais in ({"id": ""}, {"id": "a b"}, {"id": "x", "etape": "fusee"}, {"id": "x", "statut": "?"}):
            with self.assertRaises(apps.FicheInvalide):
                apps.valider(mauvais)

    def test_alerte_seulement_si_changement_et_plus_recente(self):
        self.assertTrue(apps.enregistrer(self.cx, FICHE, "depot"))
        self.assertEqual(len(alertes_apps(self.cx)), 1)
        self.assertEqual(apps.enregistrer(self.cx, FICHE, "depot"), [])  # relue : rien de neuf
        plus_vieille = dict(FICHE, etape="tests", maj_le="2026-11-01T00:00:00Z")
        self.assertEqual(apps.enregistrer(self.cx, plus_vieille, "api"), [])
        self.assertEqual(apps.lister(self.cx)[0]["etape"], "cadrage")
        bloquee = dict(FICHE, etape="design", blocages=["Clé LiveKit"], maj_le="2026-11-23T00:00:00Z")
        ch = apps.enregistrer(self.cx, bloquee, "api")
        self.assertIn("Nouveau blocage : Clé LiveKit", ch)
        self.assertEqual(len(alertes_apps(self.cx)), 2)
        # aucune alerte Apps sur le canal du bot Immobilier
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM alertes WHERE canal='telegram'").fetchone()[0], 0)

    def test_synchronisation_locale_et_distante(self):
        racine = Path(tempfile.mkdtemp())
        (racine / "apps" / "kapara").mkdir(parents=True)
        (racine / "apps" / "kapara" / "statut.json").write_text(json.dumps(FICHE), encoding="utf-8")
        (racine / "apps" / "kapara" / "app.json").write_text(
            json.dumps({"source": {"depot": "x/KAPARA", "chemin": "status/kapara.json"}}), encoding="utf-8")
        (racine / "apps" / "casse").mkdir()
        (racine / "apps" / "casse" / "statut.json").write_text("{", encoding="utf-8")
        distante = dict(FICHE, avancement=40, maj_le="2026-11-24T00:00:00Z")
        lus = []
        lire = lambda depot, chemin: lus.append((depot, chemin)) or json.dumps(distante)  # noqa: E731
        apps.synchroniser(self.cx, racine, lire)
        self.assertEqual(lus, [("x/KAPARA", "status/kapara.json")])
        self.assertEqual(apps.lister(self.cx)[0]["avancement"], 40)
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM journal WHERE niveau='erreur'").fetchone()[0], 1)

        def en_panne(depot, chemin):
            raise urllib.error.URLError("hors ligne")
        apps.synchroniser(self.cx, racine, en_panne)  # ne lève pas, note l'erreur
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM journal WHERE niveau='erreur'").fetchone()[0], 3)


class TestSeparationImmo(unittest.TestCase):
    def setUp(self):
        self.cx = connexion(":memory:")
        self.c = config_test()

    def test_bot_apps_separe(self):
        apps.enregistrer(self.cx, FICHE, "depot")
        api = FauxTelegram()
        bot = BotApps(self.cx, self.c, api)
        api.a_livrer = [msg(1, "/apps"), msg(2, "/app kapara"), msg(3, "/blocages"), msg(4, "Ajoute le mode sombre"),
                        msg(5, "/apps", de="999")]
        bot.relever()
        t = api.textes()
        self.assertIn("KAPARA : cadrage, 10 %", t[0])
        self.assertIn("Prochaine étape", t[1])
        self.assertEqual(t[2], "Aucun blocage côté Apps.")
        self.assertIn("Consigne enregistrée", t[3])
        self.assertEqual(len(t), 4)  # l'inconnu est ignoré
        tache = self.cx.execute("SELECT * FROM taches WHERE type='consigne'").fetchone()
        self.assertEqual((tache["activite"], tache["agent"]), ("apps", "apps-coordination"))
        # décalages de lecture distincts : le bot Immobilier ne relit pas ces messages comme déjà traités
        from app.db import reglage
        self.assertEqual(reglage(self.cx, "telegram_apps_offset"), "6")
        self.assertIsNone(reglage(self.cx, "telegram_offset"))

    def test_bot_immo_ne_montre_pas_les_apps(self):
        BotApps(self.cx, self.c, FauxTelegram()).traiter(msg(1, "Prépare les maquettes"))
        api = FauxTelegram()
        bot = Bot(self.cx, self.c, api)
        self.assertEqual(bot.liste_taches(), "Aucune tâche ouverte.")
        self.assertNotIn("Cheffe de projet Apps", bot.etat("immo"))
        self.assertNotIn("Prépare les maquettes", recap.generer(self.cx, self.c))

    def test_recap_apps_et_envoi_par_le_bon_bot(self):
        from datetime import datetime, timezone
        apps.enregistrer(self.cx, FICHE, "depot")
        programmer_recap(self.cx, self.c, now=datetime(2026, 11, 22, 9, 0, tzinfo=timezone.utc))
        from app import taches
        taches.executer_en_attente(self.cx, executeurs(self.c))
        corps = [a["corps"] for a in alertes_apps(self.cx)]
        self.assertTrue(any(c.startswith("Apps – récap du 22/11/2026") for c in corps))
        self.c.mode_envoi = "reel"
        immo, apps_bot = FauxEnvoi(), FauxEnvoi()
        alertes.expedier(self.cx, self.c, telegram=immo, telegram_apps=apps_bot)
        self.assertTrue(apps_bot.recus and all("Apps" in x or "KAPARA" in x for x in apps_bot.recus))
        self.assertFalse(any("KAPARA" in x for x in immo.recus))
        # sans bot Apps configuré : échec noté, jamais de repli sur le bot Immobilier
        apps.enregistrer(self.cx, dict(FICHE, statut="en_pause", maj_le="2026-11-25T00:00:00Z"), "api")
        immo2 = FauxEnvoi()
        alertes.expedier(self.cx, self.c, telegram=immo2, telegram_apps=None)
        self.assertEqual(immo2.recus, [])
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM alertes WHERE canal='telegram_apps' AND statut='echec'").fetchone()[0], 1)


class FauxEnvoi:
    def __init__(self):
        self.recus = []

    def envoyer(self, texte, boutons=None):
        self.recus.append(texte)


class TestMigrationEtEtat(unittest.TestCase):
    def test_ancienne_base_migree(self):
        chemin = Path(tempfile.mkdtemp()) / "b.sqlite3"
        old = sqlite3.connect(str(chemin))
        old.execute("""CREATE TABLE alertes (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            canal TEXT NOT NULL CHECK (canal IN ('telegram','email')), cle_unique TEXT UNIQUE NOT NULL, destinataire TEXT,
            sujet TEXT, corps TEXT NOT NULL, statut TEXT NOT NULL CHECK (statut IN ('preparee','envoyee','echec')),
            tentatives INTEGER NOT NULL DEFAULT 0, erreur TEXT, prospect_id TEXT, cree_le TEXT NOT NULL, envoyee_le TEXT)""")
        old.execute("INSERT INTO alertes (type, canal, cle_unique, corps, statut, cree_le) VALUES ('x','telegram','k','c','preparee','t')")
        old.commit()
        old.close()
        cx = connexion(chemin)
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM alertes").fetchone()[0], 1)
        self.assertTrue(alertes.preparer(cx, type="app_maj", canal="telegram_apps", cle="k2", corps="c"))

    def test_etat_complet_et_registre(self):
        cx = connexion(":memory:")
        c = config_test()
        apps.enregistrer(cx, FICHE, "depot")
        e = etat_complet(cx, c)
        self.assertEqual(e["apps"][0]["nom"], "KAPARA")
        self.assertIn("telegram_apps", e["service"])
        reg = charger_registre()
        ids_apps = {a["id"] for a in reg["agents"] if a.get("activite") == "apps"}
        self.assertEqual(ids_apps, {"apps-coordination", "apps-produit", "apps-design", "apps-dev", "apps-qualite", "apps-publication"})
        racine = Path(__file__).resolve().parents[2]
        for a in ids_apps:
            self.assertTrue((racine / "apps" / "agents" / f"{a}.md").exists(), a)
        apps.valider(json.loads((racine / "apps" / "kapara" / "statut.json").read_text(encoding="utf-8")))


class TestPointEntreeApps(unittest.TestCase):
    def test_api_statut(self):
        from http.server import ThreadingHTTPServer
        cx = connexion(":memory:")
        c = config_test(dashboard_mot_de_passe="m", jeton_apps="jeton-apps")
        srv = ThreadingHTTPServer(("127.0.0.1", 0), fabrique(cx, c))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/apps/statut"

        def post(corps, jeton):
            r = urllib.request.Request(base, data=json.dumps(corps).encode(), headers={"X-Jeton": jeton})
            try:
                with urllib.request.urlopen(r) as rep:
                    return rep.status, json.loads(rep.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        try:
            self.assertEqual(post(FICHE, "faux")[0], 401)
            self.assertEqual(post({"id": "x", "etape": "fusee"}, "jeton-apps")[0], 400)
            code, rep = post(FICHE, "jeton-apps")
            self.assertEqual(code, 200)
            self.assertTrue(rep["changements"])
            # le tableau de bord, lui, reste protégé par le mot de passe
            r = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}/api/etat",
                                       headers={"Authorization": "Basic " + base64.b64encode(b"a:m").decode()})
            with urllib.request.urlopen(r) as rep:
                self.assertEqual(json.loads(rep.read())["apps"][0]["id"], "kapara")
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()
