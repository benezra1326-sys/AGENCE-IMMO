"""Auditeur (ChatGPT) : deuxième avis indépendant sur chaque contenu « à valider », avant la décision d'Avishay.

Lit les tâches <depot>/ops/taches/*.json dont contenu.statut vaut a_valider, joint le texte des fichiers .md listés,
et demande à l'API OpenAI un avis structuré. Écrit un fichier JSON {"A-<id contenu>": avis} à recopier dans la
collection `avis` du back-office (ArtifactData batch). La clé est lue dans OPENAI_API_KEY (réglages du projet),
jamais écrite nulle part. Seuls les contenus à publier sont envoyés : jamais de prospects ni de clients.

Usage :
  python3 -m scripts.auditer --depot /tmp/claude-0/m3 --sortie avis.json [--seulement <id>] [--modele gpt-4.1]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REGLES = """Tu es l'auditeur indépendant et le bras droit d'Avishay Benazra, agent immobilier de luxe chez Levy & Goldman à Marbella.
Une équipe d'agents IA prépare ses contenus (Reels, carrousels, posts LinkedIn, messages WhatsApp aux agents partenaires).
Tu relis chaque contenu AVANT qu'Avishay décide, et tu lui donnes ton avis franc, en français, en le tutoyant.
Règles de la marque à vérifier :
- ton premium, sobre, professionnel, aucun humour ;
- zone : « Marbella et ses alentours, jusqu'à Estepona » ; jamais de nom de bien ou de programme, ni d'adresse ;
- aucun chiffre ni loi sans source citée ; aucune promesse de rendement, de financement ou de licence touristique ;
- jamais de pourcentage de commission ; pas d'email de prospection à froid (loi espagnole LSSI art. 21) ;
- cibles : francophones (France, Belgique, Suisse, Maroc), puis Royaume-Uni ; apporteurs d'affaires (agents, chasseurs, conseillers).
Réponds UNIQUEMENT en JSON : {"note": entier 1-10, "verdict": "publier" | "a_retoucher" | "a_refaire",
"resume": une phrase, "points_forts": [max 3], "a_corriger": [max 4, concrets], "risques": [règles non respectées, vide si aucun],
"suggestion": une proposition de réécriture courte de l'accroche ou du passage le plus faible}."""


DIRECTIVES = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "directives-avishay" / "SKILL.md"


def regles() -> str:
    d = DIRECTIVES.read_text(encoding="utf-8") if DIRECTIVES.exists() else ""
    return REGLES + ("\n\nSes directives détaillées (goûts et refus, à jour) :\n" + d if d else "")


def contenus(depot: Path, seul: str | None):
    for f in sorted((depot / "ops" / "taches").glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        c = t.get("contenu") or {}
        if c.get("statut") != "a_valider" or (seul and t["id"] != seul):
            continue
        textes = []
        for p in t.get("fichiers", []):
            q = depot / p
            if q.suffix == ".md" and q.exists():
                textes.append(q.read_text(encoding="utf-8")[:12000])
        yield t, c, "\n\n".join(textes)


def demander(modele: str, cle: str, t: dict, c: dict, texte: str) -> dict:
    corps = {
        "model": modele,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": regles()},
            {"role": "user", "content": f"Contenu : {c.get('titre')}\nFormat : {c.get('format')} · langue {c.get('langue')}\n"
                                        f"Compte rendu de l'équipe : {t.get('resultat', '')}\n\nTexte et notes :\n{texte or '(aucun texte joint, seulement des visuels)'}"},
        ],
    }
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(corps).encode(),
                                 headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rep = json.loads(r.read())
    avis = json.loads(rep["choices"][0]["message"]["content"])
    avis.update(par="chatgpt", contenu="C-" + t["id"], modele=rep.get("model", modele), quand=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    return avis


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--depot", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--seulement")
    ap.add_argument("--modele", default=os.environ.get("OPENAI_MODEL", "gpt-4.1"))
    a = ap.parse_args()
    brut = os.environ.get("OPENAI_API_KEY", "")
    m = re.search(r"sk-[A-Za-z0-9_\-]{20,}", brut)  # tolère un texte collé autour de la clé dans les réglages
    cle = m.group(0) if m else brut.strip()
    if not cle:
        sys.exit("OPENAI_API_KEY absente : à ajouter dans les réglages du projet (une nouvelle session la lit).")
    res = {}
    for t, c, texte in contenus(Path(a.depot), a.seulement):
        try:
            res["A-" + t["id"]] = demander(a.modele, cle, t, c, texte)
            print("OK", t["id"], res["A-" + t["id"]].get("note"))
        except urllib.error.HTTPError as e:  # le code d'erreur OpenAI (ex. crédits épuisés), jamais la clé
            try:
                code = json.loads(e.read()).get("error", {}).get("code")
            except Exception:
                code = None
            print("ECHEC", t["id"], e.code, code or "")
        except Exception as e:  # une erreur sur un contenu n'arrête pas les autres ; la clé n'est jamais affichée
            print("ECHEC", t["id"], type(e).__name__)
    Path(a.sortie).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
