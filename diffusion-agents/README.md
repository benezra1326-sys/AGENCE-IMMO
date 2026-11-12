# Diffusion des nouveaux biens aux agents partenaires (WhatsApp)

Chaîne : **Excel → window card (PDF + aperçu) → lot à valider → OK d'Avishay → WhatsApp**.
Mode validation : rien ne part sans son OK, et seulement aux agents qui ont accepté de recevoir les fiches.

| Étape | Fichier | Ce qui se passe |
| --- | --- | --- |
| 1 | `biens-et-agents.xlsx` (créé par `creer_classeur.py`) | Avishay ajoute un bien dans « Biens » avec le statut **Nouveau**. Feuille « Agents » : un agent par ligne, avec son accord WhatsApp (oui/non, date, comment). |
| 2 | `generer.py` | Pour chaque bien « Nouveau » : window card A4 (PDF) + PNG, message FR/EN/ES par agent, `lot.json` au statut `a_valider`. Les agents sans accord sont listés à part, jamais contactés. |
| 3 | back-office / Telegram | Avishay voit l'aperçu et la liste des destinataires, répond OK ou demande une modification. Le lot passe à `valide`. |
| 4 | `envoyer_whatsapp.py` | Simulation par défaut. Envoi réel avec `--confirme` et un lot `valide` : modèle Meta approuvé, fiche PDF en en-tête. |

Commandes :
```
python3 creer_classeur.py biens-et-agents.xlsx --dossier-photos-ab0002 /mnt/project-files/agence-immo/medias/AB-0002
python3 generer.py biens-et-agents.xlsx sortie/
python3 envoyer_whatsapp.py sortie/AB-0002/lot.json            # simulation
python3 envoyer_whatsapp.py sortie/AB-0002/lot.json --confirme # après OK, lot « valide »
```
Rendu : Node + Playwright (`rendu.js`), polices Google Fonts (Montserrat, Cormorant Garamond).

## Règles
- Jamais de pourcentage de commission sur la fiche ni dans le message.
- Fiche B2B : zone, typologie, chiffres, prix. Pas de nom de programme, d'architecte ni d'adresse.
- WhatsApp (règles Meta) : pour écrire en premier, il faut un modèle approuvé et l'accord de la personne ; chaque message dit comment se désinscrire (STOP).
- Le texte `message` du lot est l'aperçu ; le texte envoyé est celui du modèle approuvé (variables : prénom, type, zone, prix).
- Secrets dans Project settings > Environment : `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` (+ `WHATSAPP_TEMPLATE`, `WHATSAPP_API_VERSION`).
