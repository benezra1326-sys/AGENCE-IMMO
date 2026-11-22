"""Crée le classeur modèle « biens-et-agents.xlsx » (feuilles Biens et Agents).

Usage : python3 creer_classeur.py <sortie.xlsx> [--dossier-photos-ab0002 CHEMIN]
La ligne AB-0002 sert d'exemple (programme neuf, New Golden Mile, chiffres du site Levy & Goldman
au 12/11/2026, à confirmer). Le seul destinataire « oui » est Avishay lui-même, pour le test.
"""
import argparse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

from generer import COLONNES_BIENS, COLONNES_AGENTS

ap = argparse.ArgumentParser()
ap.add_argument("sortie")
ap.add_argument("--dossier-photos-ab0002", default="photos/AB-0002")
a = ap.parse_args()

wb = Workbook()
entete = Font(bold=True, color="FFFFFF")
fond = PatternFill("solid", fgColor="15171B")


def feuille(ws, colonnes, lignes, largeur=18):
    ws.append(colonnes)
    for c in ws[1]:
        c.font, c.fill = entete, fond
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for l in lignes:
        ws.append(l)
    for i, _ in enumerate(colonnes, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = largeur
    ws.freeze_panes = "A2"


ws = wb.active
ws.title = "Biens"
feuille(ws, COLONNES_BIENS, [[
    "Nouveau", "AB-0002", "Résidence neuve", "Neuf", "New Golden Mile, Estepona", 745000, 1595000, "2–3",
    "2–3", "149–399", None, None,
    "Three pools; Spa and gym; 24h security; 27,000 m² tropical gardens; Resort services",
    a.dossier_photos_ab0002, "exteriors-cam03-12142021.jpg; terrace-pool-12162021.jpg; living-09252018.jpg",
    "2026-11-12", None,
]])
dv = DataValidation(type="list", formula1='"Nouveau,À valider,Envoyé,Retiré"', allow_blank=True)
ws.add_data_validation(dv); dv.add("A2:A500")
dv2 = DataValidation(type="list", formula1='"Neuf,Revente"', allow_blank=True)
ws.add_data_validation(dv2); dv2.add("D2:D500")

wg = wb.create_sheet("Agents")
feuille(wg, COLONNES_AGENTS, [
    ["Avishay (test)", "Levy & Goldman", "Marbella", "Espagne", "+34647142274", "FR", "oui", "2026-11-12",
     "Numéro d'Avishay, pour tester", "oui"],
    ["Exemple Agent", "Agence exemple", "Paris", "France", "+33600000000", "FR", "non", None,
     "À remplir : message, email ou formulaire où l'agent a dit oui", "oui"],
])
for col in ("G", "J"):
    v = DataValidation(type="list", formula1='"oui,non"', allow_blank=True)
    wg.add_data_validation(v); v.add(f"{col}2:{col}500")
v = DataValidation(type="list", formula1='"FR,EN,ES"', allow_blank=True)
wg.add_data_validation(v); v.add("F2:F500")

wb.save(a.sortie)
print("Classeur créé :", a.sortie)
