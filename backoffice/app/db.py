"""Base de données du back-office (SQLite, un seul fichier sur le serveur).

Les contraintes UNIQUE portent la prévention des doublons :
- taches.cle_unique : une même demande ne crée pas deux tâches ;
- interactions.cle_unique : un même message reçu deux fois n'est enregistré qu'une fois ;
- identifiants.valeur : un même email / téléphone / compte ne crée pas deux fiches ;
- alertes.cle_unique : une même alerte (type + prospect + canal) n'est préparée qu'une fois.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS taches (
    id TEXT PRIMARY KEY,
    activite TEXT NOT NULL,
    agent TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'manuelle',
    titre TEXT NOT NULL,
    statut TEXT NOT NULL CHECK (statut IN ('en_attente','en_cours','terminee','echec','bloquee')),
    source TEXT,
    cree_le TEXT NOT NULL,
    maj_le TEXT NOT NULL,
    resultat TEXT,
    fichiers TEXT NOT NULL DEFAULT '[]',
    cout_eur REAL NOT NULL DEFAULT 0,
    raison_echec TEXT,
    tentatives INTEGER NOT NULL DEFAULT 0,
    max_tentatives INTEGER NOT NULL DEFAULT 3,
    prochain_essai TEXT,
    cle_unique TEXT UNIQUE,
    origine TEXT NOT NULL DEFAULT 'serveur',
    donnees TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS contenus (
    id TEXT PRIMARY KEY,
    tache_id TEXT,
    activite TEXT NOT NULL DEFAULT 'immo',
    titre TEXT NOT NULL,
    format TEXT,
    langue TEXT,
    statut TEXT NOT NULL CHECK (statut IN ('en_preparation','brouillon','a_valider','modification_demandee','valide','publie','remplace')),
    date_prevue TEXT,
    bien TEXT,
    fichiers TEXT NOT NULL DEFAULT '[]',
    maj_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS retours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contenu_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('valide','modification')),
    texte TEXT,
    canal TEXT NOT NULL,
    cree_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prospects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'acheteur',
    nom TEXT,
    source TEXT,
    pays TEXT,
    langue TEXT,
    budget TEXT,
    zone TEXT,
    delai TEXT,
    projet TEXT,
    statut TEXT NOT NULL DEFAULT 'nouveau',
    appel_demande INTEGER NOT NULL DEFAULT 0,
    fictif INTEGER NOT NULL DEFAULT 0,
    cree_le TEXT NOT NULL,
    maj_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS identifiants (
    valeur TEXT PRIMARY KEY,
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    genre TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_id TEXT NOT NULL REFERENCES prospects(id),
    canal TEXT NOT NULL,
    sens TEXT NOT NULL CHECK (sens IN ('entrant','sortant','note')),
    texte TEXT,
    cle_unique TEXT UNIQUE,
    cree_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alertes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    canal TEXT NOT NULL CHECK (canal IN ('telegram','email')),
    cle_unique TEXT UNIQUE NOT NULL,
    destinataire TEXT,
    sujet TEXT,
    corps TEXT NOT NULL,
    statut TEXT NOT NULL CHECK (statut IN ('preparee','envoyee','echec')),
    tentatives INTEGER NOT NULL DEFAULT 0,
    erreur TEXT,
    prospect_id TEXT,
    cree_le TEXT NOT NULL,
    envoyee_le TEXT
);
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quand TEXT NOT NULL,
    niveau TEXT NOT NULL DEFAULT 'info' CHECK (niveau IN ('info','erreur')),
    acteur TEXT NOT NULL,
    action TEXT NOT NULL,
    objet TEXT,
    details TEXT
);
CREATE TABLE IF NOT EXISTS couts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quand TEXT NOT NULL,
    poste TEXT NOT NULL,
    montant_eur REAL NOT NULL,
    tache_id TEXT,
    details TEXT
);
CREATE TABLE IF NOT EXISTS reglages (
    cle TEXT PRIMARY KEY,
    valeur TEXT
);
"""


def maintenant():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connexion(chemin):
    chemin = Path(chemin)
    if str(chemin) != ":memory:":
        chemin.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(str(chemin), check_same_thread=False, isolation_level=None)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA foreign_keys = ON")
    if str(chemin) != ":memory:":
        cx.execute("PRAGMA journal_mode = WAL")
    cx.executescript(SCHEMA)
    return cx


def ligne(row):
    if row is None:
        return None
    d = dict(row)
    for champ in ("fichiers", "donnees"):
        if champ in d and isinstance(d[champ], str):
            try:
                d[champ] = json.loads(d[champ])
            except ValueError:
                pass
    return d


def journaliser(cx, acteur, action, objet=None, details=None, niveau="info"):
    cx.execute(
        "INSERT INTO journal (quand, niveau, acteur, action, objet, details) VALUES (?,?,?,?,?,?)",
        (maintenant(), niveau, acteur, action, objet, details),
    )


def reglage(cx, cle, defaut=None):
    row = cx.execute("SELECT valeur FROM reglages WHERE cle=?", (cle,)).fetchone()
    return row["valeur"] if row else defaut


def ecrire_reglage(cx, cle, valeur):
    cx.execute(
        "INSERT INTO reglages (cle, valeur) VALUES (?,?) ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
        (cle, valeur),
    )
