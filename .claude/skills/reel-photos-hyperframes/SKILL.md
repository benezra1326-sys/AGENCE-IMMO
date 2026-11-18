---
name: reel-photos-hyperframes
description: Fabriquer un Reel immo 9:16 à partir de photos fixes (ou de plans vidéo) avec HyperFrames, dans le style d'Avishay. À lire avant tout Reel fait sans tournage, à partir des photos d'un bien.
---

# Reel à partir de photos (HyperFrames)

Validé par Avishay le 18/11/2026 : « tu pourras prendre des photos et créer des Reels avec ça ».
HyperFrames (HeyGen, open source) transforme une page HTML animée en MP4. Lire aussi la skill `/hyperframes` (contrat de rendu) avant d'écrire.

## Ce qu'on fait
Des photos fixes d'un bien deviennent un Reel : zoom lent (Ken Burns) sur chaque photo, textes qui apparaissent, enchaînements en fondu, carte de fin Levy & Goldman. Modèle de départ : `modele-reel.html` (14 s, 5 photos + carte de fin).

## Règles (non négociables)
1. **Netteté** : photos d'au moins 1080 × 1920 en vertical (ou 2000 px de haut). Jamais de photo 1080 × 1350 agrandie : la démo du 18/11 était floue pour cette raison. Sinon, préférer les plans vidéo HD du Dropbox.
2. **Zoom** : 1,00 → 1,06 maximum, sur une image déjà assez grande. Pas d'agrandissement supplémentaire.
3. **Textes** : Montserrat, majuscules, blanc, sans encadré noir. Serif uniquement sur la carte de fin noire LEVY & GOLDMAN (logo officiel : `marque/levy-goldman-logo-blanc.png`).
4. **Contenu des textes** : jamais le nom de la villa ni rien qui permette de la retrouver ; zone seulement (« Marbella et alentours, jusqu'à Estepona »). Pas de prix, chambres ou m² inventés : seulement ce qu'Avishay a confirmé, sinon « price on request ». Sinon textes généraux. Anglais d'abord, puis FR/ES.
5. **Musique** : obligatoire, choisie selon la skill `musique-reels` (3 options + recommandation). Avishay l'écoute avant publication.
6. **Ton** : skill `ton-marque` (premium, sobre, aucun humour).
7. **Mode validation** : rien n'est publié. Le MP4 va dans les contenus « à valider » avec une légende.

## Rendu
`npx hyperframes lint` puis `npx hyperframes render -o reel.mp4`. Contrôler 4 ou 5 images extraites (ffmpeg) avant d'envoyer : netteté, texte lisible, aucun nom de bien.
Sur le Mac d'Avishay : HyperFrames, FFmpeg et FFprobe sont installés (~/.local/bin).
