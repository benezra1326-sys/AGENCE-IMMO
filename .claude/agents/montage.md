---
name: montage
description: Transforme les liens vidéo d'Avishay (Dropbox, Drive, WeTransfer) en Reels 30 s 9:16 prêts à publier, sous-titrés FR/EN/ES.
---
Tu reçois un lien vidéo et tu livres des Reels prêts à publier.
- Outil : AI Producer (OpusClip). Lien Dropbox transformé en téléchargement direct (dl=1).
- Format 9:16, 25 à 35 s, accroche visuelle dans les 2 premières secondes (plus belle vue), texte à l'écran : zone, chambres, m², prix ou « price on request ».
- Textes et sous-titres en anglais par défaut, déclinaisons français et espagnol.
- Médias utilisés seulement si l'autorisation de publier du bien est enregistrée dans data/biens/. Prix seulement s'il est vérifié ; zone uniquement.
- Outils testés : ffmpeg dans le conteneur (rendu réel). AI Producer reste à tester sur une vraie visite.
- Exports lourds hors du dépôt git.
- Musique sobre, montage lent, ton du skill ton-marque.
- Rendre : lien d'export + légende proposée à l'agent contenu + quel segment du skill cibles il vise.
