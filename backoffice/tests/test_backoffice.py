import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import alertes, commissions, leads, pilotage, recap, taches
from app.config import Config
from app.db import connexion
from app.registre import etat_complet, synchroniser_depot
from app.serveur import fabrique
from app.service import executeurs, programmer_recap
from app.telegram_bot import Bot

PROPRIO = "111222333"


def config_test(**kw):
    c = Config()
    c.mode_envoi = "test"
    c.telegram_token = None
    c.telegram_proprietaire = PROPRIO
    c.racine_depot = Path(tempfile.mkdtemp())
    for k, v in kw.items():
        setattr(c, k, v)
    return c


class FauxTelegram:
    def __init__(self):
        self.envoyes, self.a_livrer = [], []

    def appel(self, methode, params):
        if methode == "getUpdates":
            out = [u for u in self.a_livrer if u["update_id"] >= params["offset"]]
            return out
        self.envoyes.append((methode, params))
        return {}

    def textes(self):
        return [p["text"] for m, p in self.envoyes if m == "sendMessage"]


def msg(uid, texte, de=PROPRIO, mid=None):
    return {"update_id": uid, "message": {"message_id": mid or uid, "from": {"id": int(de)},
                                          "chat": {"id": int(de)}, "text": texte}}


class TestTaches(unittest.TestCase):
    def setUp(self):
        self.cx = connexion(":memory:")

    def test_pas_de_doublon(self):
        t1, c1 = taches.creer(self.cx, activite="immo", agent="montage", titre="Reel", cle_unique="k1")
        t2, c2 = taches.creer(self.cx, activite="immo", agent="montage", titre="Reel bis", cle_unique="k1")
        self.assertTrue(c1)
        self.assertFalse(c2)
        self.assertEqual(t1["id"], t2["id"])
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM taches").fetchone()[0], 1)

    def test_reprise_puis_echec(self):
        t, _ = taches.creer(self.cx, activite="immo", agent="montage", titre="x", cle_unique="k2", type="boum",
                            max_tentatives=3)

        def boum(cx, t):
            raise RuntimeError("panne réseau")

        now = datetime.now(timezone.utc)
        taches.executer_en_attente(self.cx, {"boum": boum})
        t = taches.obtenir(self.cx, t["id"])
        self.assertEqual((t["statut"], t["tentatives"]), ("en_attente", 1))
        self.assertIsNotNone(t["prochain_essai"])
        # pas de nouvel essai avant l'échéance
        self.assertEqual(taches.executer_en_attente(self.cx, {"boum": boum}, now.isoformat()), [])
        loin = (now + timedelta(hours=1)).isoformat()
        taches.executer_en_attente(self.cx, {"boum": boum}, loin)
        taches.executer_en_attente(self.cx, {"boum": boum}, (now + timedelta(hours=2)).isoformat())
        t = taches.obtenir(self.cx, t["id"])
        self.assertEqual((t["statut"], t["tentatives"]), ("echec", 3))
        self.assertIn("panne réseau", t["raison_echec"])
        self.assertTrue(taches.reprendre(self.cx, t["id"]))
        self.assertEqual(taches.obtenir(self.cx, t["id"])["statut"], "en_attente")

    def test_connexion_manquante_bloque(self):
        t, _ = taches.creer(self.cx, activite="immo", agent="instagram", titre="Publier", cle_unique="k3", type="pub")

        def pub(cx, t):
            raise taches.ConnexionManquante("Instagram non relié à une page Facebook")

        taches.executer_en_attente(self.cx, {"pub": pub})
        self.assertEqual(taches.obtenir(self.cx, t["id"])["statut"], "bloquee")

    def test_double_demarrage_impossible(self):
        t, _ = taches.creer(self.cx, activite="immo", agent="montage", titre="x", cle_unique="k4")
        self.assertTrue(taches.demarrer(self.cx, t["id"]))
        self.assertFalse(taches.demarrer(self.cx, t["id"]))


class TestImportDepot(unittest.TestCase):
    def test_import_idempotent_et_contenu(self):
        cx, c = connexion(":memory:"), config_test()
        d = c.racine_depot / "ops" / "taches"
        d.mkdir(parents=True)
        fiche = {"id": "2026-11-09-reel-aloha40", "activite": "immo", "agent": "montage", "titre": "Reel Aloha 40",
                 "statut": "terminee", "source": "brief", "cree_le": "2026-11-09T11:00:00+00:00",
                 "maj_le": "2026-11-09T12:00:00+00:00", "resultat": "MP4 32 s", "fichiers": ["livrables/a.mp4"],
                 "cout_eur": 0, "raison_echec": None,
                 "contenu": {"titre": "Reel Aloha 40", "format": "reel", "langue": "en", "statut": "a_valider",
                             "date_prevue": "2026-11-12", "bien": "SV2342"}}
        (d / "2026-11-09-reel-aloha40.json").write_text(json.dumps(fiche), encoding="utf-8")
        (d / "cassee.json").write_text("{pas du json", encoding="utf-8")
        synchroniser_depot(cx, c.racine_depot)
        synchroniser_depot(cx, c.racine_depot)
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM taches").fetchone()[0], 1)
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM contenus").fetchone()[0], 1)
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM journal WHERE niveau='erreur'").fetchone()[0], 2)
        # la décision d'Avishay n'est pas écrasée par une nouvelle synchronisation
        pilotage.valider_contenu(cx, "C-2026-11-09-reel-aloha40", "test")
        synchroniser_depot(cx, c.racine_depot)
        self.assertEqual(cx.execute("SELECT statut FROM contenus").fetchone()[0], "valide")
        # l'agent montage passe à « testé » grâce à une tâche réellement terminée
        etat = etat_complet(cx, c)
        montage = next(a for a in etat["agents"] if a["id"] == "montage")
        self.assertEqual(montage["etat"], "teste")


class TestProspects(unittest.TestCase):
    def setUp(self):
        self.cx, self.c = connexion(":memory:"), config_test()

    def nb(self, table, where="1=1"):
        return self.cx.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]

    def test_parcours(self):
        r1 = leads.recevoir(self.cx, self.c, canal="formulaire", message_id="m1", nom="Claire Test",
                            email="Claire.Test@Example.com", langue="fr", pays="FR", fictif=True,
                            texte="Bonjour, nous cherchons une résidence secondaire à Nueva Andalucía, budget 2,5 M€.")
        self.assertEqual(r1["resultat"], "nouveau_prospect")
        self.assertEqual(r1["alertes"], 2)
        p = self.cx.execute("SELECT * FROM prospects").fetchone()
        self.assertEqual((p["budget"], p["projet"], p["zone"]), ("2.5 M€", "residence_secondaire", "Nueva Andalucía"))
        # même message rejoué -> ignoré
        self.assertEqual(leads.recevoir(self.cx, self.c, canal="formulaire", message_id="m1", texte="x")["resultat"],
                         "doublon_message")
        # nouvel échange, email écrit autrement -> même fiche, pas de nouvelle alerte
        r2 = leads.recevoir(self.cx, self.c, canal="email", message_id="m2", email=" claire.test@example.COM ",
                            telephone="+33 6 12 34 56 78", texte="Nous pourrions venir en janvier.")
        self.assertEqual((r2["resultat"], r2["alertes"]), ("fiche_enrichie", 0))
        # demande d'appel -> alerte immédiate, une seule fois
        r3 = leads.recevoir(self.cx, self.c, canal="whatsapp", message_id="m3", telephone="0033612345678",
                            texte="Pouvez-vous m'appeler demain matin ?")
        self.assertEqual((r3["resultat"], r3["alertes"]), ("fiche_enrichie", 2))
        r4 = leads.recevoir(self.cx, self.c, canal="whatsapp", message_id="m4", telephone="+33612345678",
                            texte="Merci de m'appeler, c'est urgent.")
        self.assertEqual(r4["alertes"], 0)
        self.assertEqual(self.nb("prospects"), 1)
        self.assertEqual(self.nb("interactions"), 4)
        self.assertEqual(self.nb("alertes"), 4)
        self.assertEqual(self.nb("alertes", "statut='preparee'"), 4)
        email = self.cx.execute("SELECT * FROM alertes WHERE canal='email' AND type='appel_demande'").fetchone()
        self.assertEqual(email["destinataire"], "avi@levygoldman.com")
        self.assertIn("[TEST - prospect fictif]", email["sujet"])

    def test_appel_des_le_premier_message(self):
        r = leads.recevoir(self.cx, self.c, canal="instagram", message_id="dm1", compte="@john.uk", langue="en",
                           texte="ALOHA – could you call me today? Budget around 3M")
        self.assertEqual(r["alertes"], 4)  # nouvelle demande + appel, chacune Telegram + email

    def test_extraction(self):
        self.assertEqual(leads.extraire("villa de 702 m² pour 800k€")["budget"], "800 k€")
        self.assertNotIn("budget", leads.extraire("à 300 m de la plage"))
        self.assertTrue(leads.extraire("¿Me puede llamar?")["appel_demande"])
        self.assertFalse(leads.extraire("Je vous écris pour un dossier")["appel_demande"])


class TestAlertes(unittest.TestCase):
    def test_mode_test_n_envoie_rien(self):
        cx, c = connexion(":memory:"), config_test()
        alertes.preparer(cx, type="x", canal="telegram", cle="a1", corps="bonjour")
        envois = []

        class T:
            def envoyer(self, texte):
                envois.append(texte)

        self.assertEqual(alertes.expedier(cx, c, telegram=T())["envoyees"], 0)
        self.assertEqual(envois, [])

    def test_mode_reel_et_reprise(self):
        cx, c = connexion(":memory:"), config_test(mode_envoi="reel")
        alertes.preparer(cx, type="x", canal="telegram", cle="a1", corps="bonjour")
        alertes.preparer(cx, type="x", canal="email", cle="a2", corps="bonjour", sujet="s", destinataire="d@x")
        envois = []

        class T:
            def envoyer(self, texte):
                envois.append(texte)

        r = alertes.expedier(cx, c, telegram=T(), email=None)
        self.assertEqual(r["envoyees"], 1)
        row = cx.execute("SELECT statut, erreur FROM alertes WHERE canal='email'").fetchone()
        self.assertEqual(row["statut"], "echec")
        self.assertIn("non configuré", row["erreur"])
        alertes.expedier(cx, c, telegram=T())
        self.assertEqual(len(envois), 1)  # l'alerte envoyée ne repart pas


class TestTelegram(unittest.TestCase):
    def setUp(self):
        self.cx, self.c = connexion(":memory:"), config_test()
        self.api = FauxTelegram()
        self.bot = Bot(self.cx, self.c, self.api)
        self.cx.execute("""INSERT INTO contenus (id, titre, format, langue, statut, maj_le)
                           VALUES ('C-1','Reel Aloha 40','reel','en','a_valider','2026-11-09')""")

    def test_inconnu_ignore(self):
        self.api.a_livrer = [msg(1, "/etat", de="999")]
        self.bot.relever()
        self.assertEqual(self.api.textes(), [])
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM journal WHERE action='accès refusé'").fetchone()[0], 1)

    def test_commandes(self):
        self.api.a_livrer = [msg(1, "/etat"), msg(2, "/etat immo"), msg(3, "/avalider"), msg(4, "/recap")]
        self.bot.relever()
        t = self.api.textes()
        self.assertIn("Immobilier Marbella", t[0])
        self.assertIn("Montage vidéo", t[1])
        self.assertIn("C-1", t[2])
        self.assertTrue(t[3].startswith("Récap du"))
        boutons = [p for m, p in self.api.envoyes if "reply_markup" in p]
        self.assertEqual(boutons[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"], "val:C-1")

    def test_consigne_sans_doublon(self):
        self.api.a_livrer = [msg(1, "Prépare un carrousel sur Estepona")]
        self.bot.relever()
        self.bot.traiter(msg(1, "Prépare un carrousel sur Estepona"))  # même message relivré
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM taches WHERE type='consigne'").fetchone()[0], 1)
        self.api.a_livrer = [msg(1, "Prépare un carrousel sur Estepona")]
        self.assertEqual(self.bot.relever(), 0)  # décalage mémorisé

    def test_consigne_adressee_a_un_agent(self):
        from app import pilotage
        t, _ = pilotage.consigne(self.cx, "Recale le Reel sur 100 BPM", "tableau de bord", agent="montage")
        self.assertEqual(t["agent"], "montage")
        t, _ = pilotage.consigne(self.cx, "Fais au mieux", "tableau de bord", agent="inconnu")
        self.assertEqual(t["agent"], "coordination")

    def test_modification_en_deux_temps_et_validation(self):
        self.bot.traiter({"update_id": 5, "callback_query": {"id": "q", "from": {"id": int(PROPRIO)},
                                                             "message": {"chat": {"id": 1}}, "data": "mod:C-1"}})
        self.bot.traiter(msg(6, "Ouvrir sur la piscine plutôt que sur l'entrée"))
        self.assertEqual(self.cx.execute("SELECT statut FROM contenus").fetchone()[0], "modification_demandee")
        self.assertEqual(self.cx.execute("SELECT COUNT(*) FROM taches WHERE type='modification_contenu'").fetchone()[0], 1)
        self.bot.traiter(msg(7, "/valider C-1"))
        self.assertEqual(self.cx.execute("SELECT statut FROM contenus").fetchone()[0], "valide")


class TestRecap(unittest.TestCase):
    def test_recap_unique_par_jour(self):
        cx, c = connexion(":memory:"), config_test()
        matin = datetime(2026, 11, 10, 7, 30, tzinfo=timezone.utc)  # 08:30 à Madrid
        programmer_recap(cx, c, matin)
        programmer_recap(cx, c, matin + timedelta(hours=2))
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM taches WHERE type='recap'").fetchone()[0], 1)
        taches.executer_en_attente(cx, executeurs(c))
        self.assertEqual(cx.execute("SELECT COUNT(*) FROM alertes WHERE type='recap'").fetchone()[0], 2)
        texte = recap.generer(cx, c)
        for rubrique in ("Productions", "À valider", "Publications", "Conversations", "Prospects",
                         "Prospection", "Tâches", "Blocages", "Coûts", "Pubs"):
            self.assertIn(rubrique, texte)

    def test_avant_l_heure(self):
        cx, c = connexion(":memory:"), config_test()
        self.assertIsNone(programmer_recap(cx, c, datetime(2026, 11, 10, 5, 0, tzinfo=timezone.utc)))


class TestCommissions(unittest.TestCase):
    def test_cas(self):
        self.assertEqual(commissions.calculer(100_000)["part_avishay"], 50_000)
        r = commissions.calculer(100_000, agence_partenaire=True)
        self.assertEqual((r["agence_partenaire"], r["recu_levy_goldman"], r["part_avishay"]), (50_000, 50_000, 25_000))
        # apporteur payé sur la part de l'agence (confirmé par Avishay le 9 novembre 2026)
        r = commissions.calculer(100_000, apporteur=True)
        self.assertEqual((r["apporteur"], r["part_avishay"], r["reste_levy_goldman"]), (10_000, 50_000, 40_000))
        r = commissions.calculer(100_000, agence_partenaire=True, apporteur=True)
        self.assertEqual((r["part_avishay"], r["reste_levy_goldman"]), (25_000, 15_000))


class TestServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from http.server import ThreadingHTTPServer
        cls.cx = connexion(":memory:")
        cls.c = config_test(dashboard_mot_de_passe="secret-test", jeton_demandes="jeton-test")
        (cls.c.racine_depot / "ops").mkdir()
        (cls.c.racine_depot / "ops" / "note.txt").write_text("ok", encoding="utf-8")
        (cls.c.racine_depot / "secret.txt").write_text("non", encoding="utf-8")
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), fabrique(cls.cx, cls.c))
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, chemin, mdp="secret-test", data=None, entetes=None):
        r = urllib.request.Request(self.base + chemin, data=json.dumps(data).encode() if data is not None else None)
        if mdp:
            r.add_header("Authorization", "Basic " + base64.b64encode(f"avishay:{mdp}".encode()).decode())
        for k, v in (entetes or {}).items():
            r.add_header(k, v)
        try:
            with urllib.request.urlopen(r) as rep:
                return rep.status, rep.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_auth(self):
        self.assertEqual(self.req("/api/etat", mdp=None)[0], 401)
        self.assertEqual(self.req("/api/etat", mdp="faux")[0], 401)
        code, corps = self.req("/api/etat")
        self.assertEqual(code, 200)
        self.assertEqual(len(json.loads(corps)["activites"]), 3)

    def test_fichiers(self):
        self.assertEqual(self.req("/fichiers/ops/note.txt"), (200, b"ok"))
        self.assertEqual(self.req("/fichiers/secret.txt")[0], 404)
        self.assertEqual(self.req("/fichiers/ops/../secret.txt")[0], 404)

    def test_demande_entrante(self):
        corps = {"canal": "site", "message_id": "w1", "nom": "Test", "email": "t@example.com", "texte": "Bonjour"}
        self.assertEqual(self.req("/api/demandes", mdp=None, data=corps)[0], 401)
        code, rep = self.req("/api/demandes", mdp=None, data=corps, entetes={"X-Jeton": "jeton-test"})
        self.assertEqual((code, json.loads(rep)["resultat"]), (200, "nouveau_prospect"))

    def test_consigne(self):
        code, rep = self.req("/api/consigne", data={"texte": "Lister 10 agences à Londres"})
        self.assertEqual(code, 200)


class TestConfidentialiteBiens(unittest.TestCase):
    def test_nom_et_ref_partenaire_jamais_affiches(self):
        from app.registre import masquer_biens, nom_agent
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data" / "biens").mkdir(parents=True)
            (Path(d) / "data" / "biens" / "registre.json").write_text(json.dumps(
                {"biens": [{"ref": "AB-0001", "ref_partenaire": "SV2342"}]}))
            etat = {"biens": [{"ref": "AB-0001", "nom": "Aloha 40", "ref_partenaire": "SV2342", "zone": "Marbella"}],
                    "taches": [{"titre": "Reel villa Aloha 40 (dossier SV2342)",
                                "fichiers": ["contenus/2026-11-09-reel-aloha40/plan.json"]}]}
            sortie = json.dumps(masquer_biens(etat, d), ensure_ascii=False)
            self.assertNotIn("Aloha", sortie)
            self.assertNotIn("aloha", sortie.replace('"chemin": "contenus/2026-11-09-reel-aloha40/plan.json"', ""))
            self.assertNotIn("SV2342", sortie)
            self.assertIn("Reel villa AB-0001 (dossier AB-0001)", sortie)
            self.assertIn('"chemin": "contenus/2026-11-09-reel-aloha40/plan.json"', sortie)
        self.assertTrue(nom_agent("coordination").startswith("Victor"))


if __name__ == "__main__":
    unittest.main()
