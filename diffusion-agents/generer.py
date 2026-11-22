"""Excel -> window cards + messages WhatsApp, prêts à valider.

Lit le classeur d'Avishay (feuilles « Biens » et « Agents »), et pour chaque bien au statut
« Nouveau » :
  1. génère la window card (PDF A4 + PNG d'aperçu) au style Levy & Goldman ;
  2. écrit le message d'accompagnement dans la langue de chaque agent (FR, EN, ES) ;
  3. écrit un lot « à valider » (lot.json) : la liste exacte de qui recevra quoi.

Rien n'est envoyé ici. L'envoi se fait avec envoyer_whatsapp.py, et seulement après le OK
d'Avishay. Seuls les agents dont la colonne « Accord WhatsApp » vaut « oui » sont inclus.
Le pourcentage de commission n'apparaît jamais (aucune colonne n'est lue pour ça).

Usage : python3 generer.py <classeur.xlsx> <dossier_sortie> [--ref AB-0002]
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from string import Template

import openpyxl

ICI = Path(__file__).resolve().parent
MODELE = ICI / "modele" / "window-card.html"
PHOTOS_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# Mention reprise de la window card Solvilla (Aloha 40) : Décret andalou 218/2005 sur
# l'information au consommateur. Adapter si l'agence fournit sa propre mention.
MENTION_NEUF = (
    "Prices do not include taxes or purchase costs: 10% VAT and AJD (1.2% of the purchase price) on new builds, "
    "plus notary and registry fees. Information subject to errors, omissions, changes, prior sale or withdrawal "
    "from the market. Information sheet available, Decree 218/2005 of 11 October."
)
MENTION_REVENTE = (
    "Prices do not include taxes or purchase costs: ITP 7%, plus notary and registry fees. Information subject to "
    "errors, omissions, changes, prior sale or withdrawal from the market. Information sheet available, "
    "Decree 218/2005 of 11 October."
)

COLONNES_BIENS = [
    "Statut", "Réf", "Type", "Neuf ou revente", "Zone", "Prix (€)", "Prix max (€)", "Chambres",
    "Salles de bain", "Construit (m²)", "Terrasse (m²)", "Terrain (m²)", "Points forts (séparés par ;)",
    "Dossier photos", "Photos choisies (3, séparées par ;)", "Ajouté le", "Envoyé le",
]
COLONNES_AGENTS = [
    "Nom", "Agence", "Ville", "Pays", "WhatsApp (+indicatif)", "Langue (FR/EN/ES)",
    "Accord WhatsApp (oui/non)", "Date de l'accord", "Comment l'accord a été donné", "Actif (oui/non)",
]

MESSAGES = {
    "FR": (
        "Bonjour {prenom},\n\nNouveau bien à proposer à vos acheteurs : {type_fr}, {zone}, {prix}.\n"
        "{resume}\nVous trouverez la fiche jointe.\n\nSi vous avez un acheteur pour ce bien, je vous organise "
        "la visite.\n\nAvishay Benazra · Levy & Goldman\n\nRépondez STOP pour ne plus recevoir ces fiches."
    ),
    "EN": (
        "Hello {prenom},\n\nNew listing to share with your buyers: {type_en}, {zone}, {prix}.\n"
        "{resume}\nThe property sheet is attached.\n\nIf you have a buyer for it, I will arrange the viewing.\n\n"
        "Avishay Benazra · Levy & Goldman\n\nReply STOP to stop receiving these sheets."
    ),
    "ES": (
        "Hola {prenom},\n\nNuevo inmueble para compartir con sus compradores: {type_es}, {zone}, {prix}.\n"
        "{resume}\nAdjunto la ficha.\n\nSi tiene un comprador, organizo la visita.\n\n"
        "Avishay Benazra · Levy & Goldman\n\nResponda STOP para dejar de recibir estas fichas."
    ),
}
TYPES = {  # type saisi en français -> (fr, en, es)
    "villa": ("une villa", "a villa", "una villa"),
    "appartement": ("un appartement", "an apartment", "un apartamento"),
    "penthouse": ("un penthouse", "a penthouse", "un ático"),
    "résidence neuve": ("une résidence neuve", "a new-build residence", "una promoción de obra nueva"),
    "terrain": ("un terrain", "a plot", "una parcela"),
    "hôtel": ("un hôtel", "a hotel", "un hotel"),
}
TYPES_EN = {
    "villa": "Villa", "appartement": "Apartment", "penthouse": "Penthouse",
    "résidence neuve": "New-build residence", "terrain": "Plot", "hôtel": "Hotel",
}


def euros(v) -> str:
    return f"€{int(float(v)):,}" if v not in (None, "") else ""


def fr(v) -> str:
    return f"{int(float(v)):,} €".replace(",", "\u202f") if v not in (None, "") else ""


def lire_feuille(ws, colonnes):
    entetes = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    manquantes = [c for c in colonnes if c not in entetes]
    if manquantes:
        sys.exit(f"Feuille « {ws.title} » : colonnes manquantes {manquantes}")
    lignes = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        d = dict(zip(entetes, row))
        if any(v not in (None, "") for v in d.values()):
            d["_ligne"] = i
            lignes.append(d)
    return lignes


def oui(v) -> bool:
    return str(v or "").strip().lower() in {"oui", "yes", "si", "sí", "x", "true", "1"}


def choisir_photos(bien, base: Path) -> list[Path]:
    dossier = Path(str(bien["Dossier photos"] or ""))
    if not dossier.is_absolute():
        dossier = base / dossier
    if not dossier.is_dir():
        sys.exit(f"{bien['Réf']} : dossier photos introuvable ({dossier})")
    choisies = [s.strip() for s in str(bien.get("Photos choisies (3, séparées par ;)") or "").split(";") if s.strip()]
    photos = [dossier / n for n in choisies] if choisies else sorted(
        p for p in dossier.iterdir() if p.suffix.lower() in PHOTOS_EXT)
    photos = [p for p in photos if p.is_file()]
    if len(photos) < 3:
        sys.exit(f"{bien['Réf']} : il faut au moins 3 photos (trouvées : {len(photos)})")
    return photos[:3]


def plage(a, b, suffixe=""):
    if a in (None, ""):
        return None
    a = f"{a:g}" if isinstance(a, float) else str(a)
    if b not in (None, ""):
        b = f"{b:g}" if isinstance(b, float) else str(b)
        return f"{a}–{b}{suffixe}"
    return f"{a}{suffixe}"


def construire(bien, base: Path, sortie: Path) -> dict:
    ref = str(bien["Réf"]).strip()
    dossier = sortie / ref
    dossier.mkdir(parents=True, exist_ok=True)
    photos = choisir_photos(bien, base)
    type_saisi = str(bien["Type"] or "villa").strip().lower()
    neuf = "neuf" in str(bien["Neuf ou revente"] or "").lower()

    chiffres = []
    for valeur, label in [
        (plage(bien["Chambres"], None), "Bedrooms"),
        (plage(bien["Salles de bain"], None), "Bathrooms"),
        (plage(bien["Construit (m²)"], None, " m²"), "Built"),
        (plage(bien["Terrasse (m²)"], None, " m²"), "Terrace"),
        (plage(bien["Terrain (m²)"], None, " m²"), "Plot"),
    ]:
        if valeur:
            chiffres.append(f"<div><b>{html.escape(valeur)}</b><span>{label}</span></div>")
    points = [p.strip() for p in str(bien["Points forts (séparés par ;)"] or "").split(";") if p.strip()][:5]

    prix_min, prix_max = bien["Prix (€)"], bien["Prix max (€)"]
    if prix_max not in (None, ""):
        prix, prix_label, prix_note = euros(prix_min), "From", f"up to {euros(prix_max)}"
    else:
        prix, prix_label, prix_note = euros(prix_min), "For sale", ""

    valeurs = {
        "photo1": photos[0].as_uri(), "photo2": photos[1].as_uri(), "photo3": photos[2].as_uri(),
        "etiquette": "New build · Exclusive to partners" if neuf else "New listing · Exclusive to partners",
        "zone": html.escape(str(bien["Zone"])),
        "type_bien": html.escape(TYPES_EN.get(type_saisi, type_saisi.title())),
        "nb_chiffres": str(max(len(chiffres), 1)),
        "chiffres": "".join(chiffres),
        "points": "".join(f"<li>{html.escape(p)}</li>" for p in points),
        "prix_label": prix_label, "prix": prix, "prix_note": prix_note,
        "ref": html.escape(ref),
        "mention": MENTION_NEUF if neuf else MENTION_REVENTE,
    }
    page = Template(MODELE.read_text(encoding="utf-8")).substitute(valeurs)
    fiche_html = dossier / f"window-card-{ref}.html"
    fiche_html.write_text(page, encoding="utf-8")
    pdf, png = dossier / f"window-card-{ref}.pdf", dossier / f"window-card-{ref}.png"
    subprocess.run(["node", str(ICI / "rendu.js"), str(fiche_html), str(pdf), str(png)], check=True)

    t = TYPES.get(type_saisi, (type_saisi,) * 3)
    resume_bits = [b for b in [
        plage(bien["Chambres"], None, " ch."), plage(bien["Construit (m²)"], None, " m²"),
    ] if b]
    prix_msg = f"à partir de {prix}" if prix_max not in (None, "") else prix
    return {
        "ref": ref, "zone": str(bien["Zone"]), "neuf": neuf, "pdf": str(pdf), "png": str(png),
        "ligne_excel": bien["_ligne"], "type": t, "prix_msg": {
            "FR": (f"à partir de {fr(prix_min)}" if prix_max not in (None, "") else fr(prix_min)), "EN": f"from {prix}" if prix_max not in (None, "") else prix,
            "ES": f"desde {prix}" if prix_max not in (None, "") else prix},
        "resume": " · ".join(resume_bits) + ("\n" if resume_bits else ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("classeur")
    ap.add_argument("sortie")
    ap.add_argument("--ref", help="ne traiter que ce bien")
    a = ap.parse_args()

    classeur = Path(a.classeur).absolute()
    wb = openpyxl.load_workbook(classeur, data_only=True)
    biens = lire_feuille(wb["Biens"], COLONNES_BIENS)
    agents = lire_feuille(wb["Agents"], COLONNES_AGENTS)

    a_traiter = [b for b in biens if str(b["Statut"] or "").strip().lower() == "nouveau"]
    if a.ref:
        a_traiter = [b for b in a_traiter if str(b["Réf"]).strip() == a.ref]
    destinataires = [g for g in agents if oui(g["Accord WhatsApp (oui/non)"]) and oui(g["Actif (oui/non)"])
                     and str(g["WhatsApp (+indicatif)"] or "").strip().startswith("+")]
    exclus = [g["Nom"] for g in agents if g not in destinataires]

    sortie = Path(a.sortie).absolute()
    lots = []
    for bien in a_traiter:
        f = construire(bien, classeur.parent, sortie)
        envois = []
        for g in destinataires:
            langue = str(g["Langue (FR/EN/ES)"] or "EN").strip().upper()
            langue = langue if langue in MESSAGES else "EN"
            prenom = str(g["Nom"]).split()[0]
            idx = {"FR": 0, "EN": 1, "ES": 2}[langue]
            texte = MESSAGES[langue].format(
                prenom=prenom, zone=f["zone"], prix=f["prix_msg"][langue], resume=f["resume"],
                type_fr=f["type"][0], type_en=f["type"][1], type_es=f["type"][2])
            envois.append({"agent": g["Nom"], "agence": g["Agence"], "whatsapp": str(g["WhatsApp (+indicatif)"]).replace(" ", ""),
                           "langue": langue, "message": texte, "fichier": f["pdf"], "_idx": idx,
                           "parametres": {"prenom": prenom, "type": f["type"][idx], "zone": f["zone"],
                                          "prix": f["prix_msg"][langue]}})
        lot = {
            "id": f"WA-{f['ref']}-{date.today().isoformat()}", "ref": f["ref"], "statut": "a_valider",
            "cree_le": date.today().isoformat(), "apercu": f["png"], "fiche_pdf": f["pdf"],
            "ligne_excel": f["ligne_excel"], "envois": [{k: v for k, v in e.items() if k != "_idx"} for e in envois],
            "agents_exclus_sans_accord": exclus,
        }
        (sortie / f["ref"] / "lot.json").write_text(json.dumps(lot, ensure_ascii=False, indent=2), encoding="utf-8")
        lots.append(lot)
        print(f"{f['ref']} : fiche {f['pdf']} ; {len(envois)} agents avec accord ; {len(exclus)} exclus")
    if not lots:
        print("Aucun bien au statut « Nouveau ».")


if __name__ == "__main__":
    main()
