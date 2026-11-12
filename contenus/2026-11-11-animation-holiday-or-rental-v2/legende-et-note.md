# Animation « Holiday home or rental investment? » – statut : à valider par Avishay

Fichiers (hors git, stockage du projet) : `/mnt/project-files/agence-immo/contenus/2026-11-09-animation-holiday-or-rental/`
- `animation-holiday-or-rental-EN.mp4` : 1080 × 1920, 18 s, H.264 + AAC, fond musical sobre composé par synthèse (aucun droit tiers).
- `animation-holiday-or-rental-EN-sans-musique.mp4` : même vidéo muette, pour ajouter un son de la bibliothèque Instagram à la publication (recommandé).
Source modifiable : `animation.html` (fonction render(t)), rendu par `outils/rendu-animation.js` puis ffmpeg.

## Déroulé
| Temps | Texte à l'écran |
| --- | --- |
| 0 – 3 s | Holiday home / or rental investment? |
| 3,3 – 6,5 s | Start with your goal. |
| 6,6 – 11 s | Two different searches : Holiday home (the area you love, the comfort you want, the time you will spend there) / Rental investment (rules, demand and total costs, checked property by property) |
| 11 – 14 s | Your goal shapes the area, the property and the budget. |
| 14,2 – 18 s | Send me your budget and project. Private message @avishay.marbella. Mention : no rental income or tourist licence is assumed. |

## Légende anglaise
Holiday home or rental investment? In Marbella, the answer changes everything: the area, the type of property, the rules to check and the real budget.

Start with your goal. Send me your budget and your project in a private message and I will come back with a clear plan, between Cabopino and Casares.

#Marbella #MarbellaRealEstate #CostaDelSol #PropertyInSpain #HolidayHome #NuevaAndalucia

## Note interne
Aucun chiffre, aucun rendement, aucune promesse de licence touristique : rien à sourcer. La mention « checked property by property » renvoie au Decreto 28/2016 (Junta de Andalucía) sans le citer à l'écran.

## V2 (11/11/2026)
Demande d Avishay : s inspirer des vidéos des autres agents, aligner police et position, enlever la musique. Refaite sur images de villa (vidéo autorisée AB-0001, aucun bien nommé), sans musique, 18,9 s, même charte que le Reel et le carrousel (outils/charte-texte.css). Texte inchangé sur le fond, mention de prudence conservée.

## V3 (11/11/2026)
Retour d Avishay sur la V2 : texte peu lisible, pas assez animé. Étude de Reels immobiliers performants (outliers Instagram/TikTok août-nov. 2026, via vidIQ) : accroche lisible dès la 1re seconde, un message par plan, texte guidé qui change avec les images. V3 : cartes sombres derrière le texte (lisibles sur toute image), mots qui arrivent un par un, listes qui se déroulent, pastilles Area / Property / Budget, bouton DM. Rendu : animation-texte.html (TRANSPARENT=1 node outils/rendu-animation.js ... 18.9 25) superposé au fond plan-fond.json. Sans musique.

## V4 (11/11/2026)
« Pas mal, on peut encore optimiser » : accroche visible dès la 1re image (pas de fondu au noir), zoom avant léger et continu sur chaque plan (zoom 0.07), cartes qui changent sur les coupes, barre de progression en haut.

## V5 (12/11/2026) – ralentie, petite musique, place pour la voix
Demande d'Avishay : trop rapide, ajouter une petite musique de fond, prévoir sa voix (Avi Voice, VoiceStudio sur son Mac).
- Vitesse 0,75 : 25,2 s au lieu de 18,9 s (images ralenties par interpolation, textes recalés). Source : `animation-texte-v5.html`.
- Même style que ses Reels publiés : écran final noir « LEVY & GOLDMAN », filet gris, « Your dream property awaits », téléphone, email, @.
- Fichiers (hors git) : `/mnt/project-files/agence-immo/contenus/2026-11-12-animation-holiday-or-rental-v5/`
  - `animation-V5-musique.mp4` : musique originale douce (composée par programme, aucun droit tiers, -20 LUFS).
  - `animation-V5-sans-musique.mp4` : pour un son Instagram ou pour poser la voix.
  - `musique-seule.wav` : la musique seule, pour le mixage avec la voix (voix à 100 %, musique baissée de 10 à 12 dB sous la voix).

### Script de voix off, calé sur la V5
| Temps (s) | Anglais | Français (Avishay enregistre en français) |
| --- | --- | --- |
| 0,3 – 3,6 | Holiday home, or rental investment? | Résidence secondaire, ou investissement locatif ? |
| 4,2 – 6,0 | Start with your goal. | Commencez par votre objectif. |
| 6,4 – 11,8 | A holiday home: the area you love, the comfort you want, your time there. | Une résidence secondaire : le quartier que vous aimez, le confort que vous voulez, le temps que vous y passerez. |
| 12,5 – 17,5 | A rental investment: local rules, real demand and total costs, checked property by property. | Un investissement locatif : les règles locales, la vraie demande et le coût total, vérifiés bien par bien. |
| 18,0 – 19,8 | Your goal shapes everything. | C'est votre objectif qui décide. |
| 20,4 – 24,8 | Send me your budget and your project. | Envoyez-moi votre budget et votre projet. |
Environ 2,3 mots par seconde en anglais : débit posé, rien d'accéléré. La version française est plus longue : si elle déborde, raccourcir la ligne de 6,4 s (« le quartier, le confort, le temps sur place »).
