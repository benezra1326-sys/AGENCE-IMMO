"""Transforme les lots WhatsApp (diffusion-agents/<ref>/lot.json) en contenus « à valider » du back-office.

Pour chaque lot au statut a_valider :
  - écrit <depot>/ops/taches/<lot id>.json (agent partenaires, contenu au format « diffusion whatsapp ») ;
  - écrit <depot>/contenus/<lot id>/legende-et-note.md : destinataires, messages, agents exclus sans accord.
La décision d'Avishay est ensuite dans la collection `decisions` du back-office, document « C-<lot id> » ;
`--reporter decisions.json` recopie cette décision dans lot.json (valide / modification_demandee + texte),
ce que lit envoyer_whatsapp.py. Rien n'est envoyé par ce script.

Usage :
  python3 -m scripts.importer_lots_whatsapp --lots /mnt/project-files/agence-immo/diffusion-agents --depot /tmp/claude-0/m3
  python3 -m scripts.importer_lots_whatsapp --lots … --reporter decisions.json   (dict id -> {statut, texte})
"""
import argparse
import json
from pathlib import Path


def note(lot: dict) -> str:
    l = [f"# Diffusion WhatsApp aux agents – {lot['ref']} – à valider par Avishay, rien n'est envoyé", "",
         f"Fiche : window card {lot['ref']} (PDF joint à chaque message). Créé le {lot.get('cree_le', '?')}.",
         f"Destinataires : {len(lot.get('envois', []))} agents qui ont donné leur accord pour recevoir nos fiches sur WhatsApp.", ""]
    for e in lot.get("envois", []):
        l += [f"## {e['agent']} ({e.get('agence') or 'agence ?'}) · {e.get('langue', '?')}", "", e.get("message", "").strip(), ""]
    ex = lot.get("agents_exclus_sans_accord") or []
    if ex:
        l += ["## Non envoyés (pas d'accord WhatsApp ou inactifs)", "", ", ".join(ex), ""]
    l += ["## Règles", "", "Envoi seulement aux agents qui ont accepté (pas de message à froid). Rien ne part sans ton OK."]
    return "\n".join(l)


def importer(lots_dir: Path, depot: Path) -> list[str]:
    faits = []
    for f in sorted(lots_dir.glob("*/lot.json")):
        lot = json.loads(f.read_text(encoding="utf-8"))
        if lot.get("statut") != "a_valider":
            continue
        lid = lot["id"]
        (depot / "contenus" / lid).mkdir(parents=True, exist_ok=True)
        (depot / "contenus" / lid / "legende-et-note.md").write_text(note(lot), encoding="utf-8")
        tache = {
            "id": lid, "agent": "partenaires", "activite": "immo", "statut": "terminee",
            "titre": f"Diffusion WhatsApp de la fiche {lot['ref']} aux agents",
            "source": f"Classeur Excel, ligne {lot.get('ligne_excel', '?')}",
            "resultat": f"Window card prête, {len(lot.get('envois', []))} agents avec accord. Rien n'est envoyé avant ton OK.",
            "fichiers": [f"contenus/{lid}/legende-et-note.md", str(f)],
            "contenu": {"titre": f"WhatsApp agents · fiche {lot['ref']} ({len(lot.get('envois', []))} destinataires)",
                        "format": "diffusion whatsapp", "langue": "multi", "statut": "a_valider", "date_prevue": None,
                        "bien": lot["ref"]},
            "raison_echec": None, "cree_le": f"{lot.get('cree_le')}T00:00:00Z", "maj_le": f"{lot.get('cree_le')}T00:00:00Z",
            "cout_eur": 0,
        }
        (depot / "ops" / "taches").mkdir(parents=True, exist_ok=True)
        (depot / "ops" / "taches" / f"{lid}.json").write_text(json.dumps(tache, ensure_ascii=False, indent=1), encoding="utf-8")
        faits.append(lid)
    return faits


def reporter(lots_dir: Path, decisions: dict) -> list[str]:
    faits = []
    for f in sorted(lots_dir.glob("*/lot.json")):
        lot = json.loads(f.read_text(encoding="utf-8"))
        d = decisions.get(f"C-{lot['id']}") or decisions.get(lot["id"])
        if not d or d.get("statut") not in ("valide", "modification_demandee") or lot.get("statut") == d["statut"]:
            continue
        lot["statut"] = d["statut"]
        lot["decision"] = {"texte": d.get("texte", ""), "quand": d.get("quand")}
        f.write_text(json.dumps(lot, ensure_ascii=False, indent=2), encoding="utf-8")
        faits.append(f"{lot['id']} -> {d['statut']}")
    return faits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lots", required=True)
    ap.add_argument("--depot")
    ap.add_argument("--reporter")
    a = ap.parse_args()
    if a.reporter:
        print("\n".join(reporter(Path(a.lots), json.loads(Path(a.reporter).read_text(encoding="utf-8")))) or "rien à reporter")
    else:
        print("\n".join(importer(Path(a.lots), Path(a.depot))) or "aucun lot à valider")
