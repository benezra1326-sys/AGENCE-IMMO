---
name: musique-reels
description: Musique des Reels villas : depuis le 22/11/2026 c'est Avishay qui choisit (il envoie un lien, souvent Spotify) ; l'agent livre sans musique, lui dit quand choisir, puis intègre ou trouve un équivalent libre de droits. À lire par montage, contenu et qualite avant toute question de musique.
---

# Musique des Reels villas

## RÈGLE EN VIGUEUR (22/11/2026) : c'est Avishay qui choisit la musique
Il ne veut plus de sélection proposée par les agents. Pour chaque vidéo :
1. Livrer la vidéo **sans musique**, montée et calée (coupes, révélations repérées).
2. Lui dire clairement **quand choisir** : « Vidéo X prête, choisis la musique ». Donner la durée, l'ambiance des images et la seconde du moment fort, pour l'aider à chercher.
3. Il envoie un lien (souvent Spotify, parfois YouTube ou Instagram).
4. Selon le lien :
   - **Spotify, ou tout titre commercial** : on ne peut pas le mettre dans le fichier (pas de licence pour une vidéo publiée par un compte pro). Deux solutions, à lui proposer en une ligne :
     a. Il ajoute le titre lui-même dans Instagram au moment de publier (bouton Audio, si le titre est disponible pour son compte ; un compte Entreprise n'a que la Meta Sound Collection). L'agent lui livre la vidéo sans musique et lui indique où caler le morceau.
     b. L'agent cherche un équivalent libre de droits (Mixkit Free License) du même style et tempo, l'intègre, et le lui fait écouter.
   - **Piste libre de droits** (Mixkit, Meta Sound Collection, musique achetée avec licence) : l'agent l'intègre directement (niveau ~-16 LUFS, fondus, moment fort calé sur la révélation, musique baissée sous la voix).
5. Rien n'est publié sans son OK.

Les sections ci-dessous restent valables comme méthode (veille, style, calage, droits), mais **on ne lui présente plus trois options** : on attend son lien.

## Méthode (règle du 18/11/2026)

But : une musique qui renforce l'émotion et le rythme du montage, sans détourner l'attention de la propriété.
À lire avec la skill directives-avishay (ses goûts et refus) et ton-marque.

## 1. Observer le marché (veille)
Comptes suivis :
| Agence | Compte Instagram |
| --- | --- |
| **Solvilla (référence n°1 d'Avishay)** | @solvillamarbella, @alex.solvilla, @stacy.solvilla, @pablo.solvilla |
| Drumelia | @drumelia_real_estate |
| Engel & Völkers Marbella | @engelvoelkers.marbella |
| MPDunne (Hamptons) | @hamptons_mpdunne |
| The Agency Marbella | @theagency.marbella |
| Mas Property Marbella | @masproperty.marbella |
| Autres grosses agences | @homerunbrokers, @marbellahillshomes, @collectiverealestate, @key_real_estate, @international_marbella, @newberyrealestate, @marbelhaus |

- Fréquence : une fois par mois, et avant chaque nouvelle série de Reels.
- Outil qui marche (vérifié le 18/11/2026) : Firecrawl, `alexandria_library_read` avec `{"provider":"scrapecreators","capability":"instagram/user-reels","options":{"handle":"<compte>"}}` (12 Reels par appel, 2 crédits). Le résultat est gros : il est enregistré dans un fichier, à lire avec jq.
  - Audio : `media.clips_metadata.audio_type` (`licensed_music` ou `original_sounds`), titre et artiste dans `clips_metadata.music_info.music_asset_info` (`title`, `display_artist`), son original dans `clips_metadata.original_sound_info.original_audio_title` et `ig_artist.username`.
  - Chiffres : `play_count`, `like_count`, `comment_count`, `taken_at`, `video_duration`. Lien : https://www.instagram.com/reel/<code>/
  - L'onglet Reels d'un compte contient aussi les collaborations : noter le vrai propriétaire (`user.username`).
- Pour chaque Reel pertinent, relever : lien, date, type de bien, style du montage, nom de l'audio affiché par Instagram, vues et interactions visibles.
- **Ne jamais inventer un titre.** « Original audio », « Mix » ou un son sans titre = **non identifié**. Un tempo mesuré par logiciel est une estimation, à écrire « environ ».
- Ranger le relevé dans `veille/musique/AAAA-MM-JJ-reels-agences.md` (lien, date, bien, montage, audio, vues).

Avishay veut des musiques **similaires à celles des grosses agences** (Solvilla d'abord) : cinéma sombre et élégant, soul/R&B chic, groove funk, lounge. Étude du 18/11 : veille/musique/2026-11-18-etude-grosses-agences.md.

## 2. Choisir selon le bien et les images
| Images | Direction musicale |
| --- | --- |
| Villa contemporaine, lignes épurées, vues mer | Électronique atmosphérique, élégante, progressive (deep house moderne et fluide, son goût) |
| Villa méditerranéenne, jardins, lumière dorée | Guitare ou piano doux, son organique, chaleureux (rester vivant : pas « salon de massage ») |
| Domaine spectaculaire, présentation très cinéma | Orchestral ou ambient avec montée graduelle |
| Visite rapide, détails design, montage dynamique | Tempo plus marqué, rythme net qui porte les coupes |
| Agent à l'image ou voix off | Musique discrète, peu ou pas de paroles, la voix reste intelligible |

## 3. Éviter les choix génériques
- Pas de musique choisie seulement parce qu'elle est tendance.
- Éviter : morceaux trop reconnaissables, paroles envahissantes, sons agressifs ou festifs, morceaux déjà vus plusieurs fois dans la veille récente (tenir la liste « déjà surutilisés » dans le relevé).
- Refus déjà exprimés par Avishay : voir directives-avishay, section Musique (house agressive, ambient calme « salon de massage »).

## 4. Caler la musique sur le montage
- Repérer le premier plan fort et les changements de scène (outil : `outils/caler_tempo.py`, détection des coupes ffmpeg scdet).
- Placer le moment le plus fort (montée, ouverture, changement de rythme) sur une révélation : arrivée sur la façade, ouverture sur la mer, découverte de la piscine, plan aérien.
- Quand quelqu'un parle : baisser la musique nettement sous la voix et vérifier à l'écoute que chaque mot se comprend.
- Niveau final autour de -14 à -16 LUFS, entrée courte, sortie en fondu.

## 5. Vérifier les droits avant publication
- Priorité aux pistes dont l'usage commercial est autorisé pour le compte et la plateforme.
- Mixkit (Stock Music Free License) : réseaux sociaux et publicités autorisés (mixkit.co/license). Musique générée vidIQ : libre de droits.
- Instagram : la bibliothèque musicale complète est réservée à l'usage personnel ; un compte professionnel Entreprise n'a que la Meta Sound Collection (help.instagram.com/402084904469945). Une publication par l'API ne permet pas d'ajouter un son de la bibliothèque : la musique doit être dans le fichier.
- Spotify : jamais intégré dans le fichier (pas de licence). Si Avishay envoie un lien Spotify : ajout par lui dans Instagram à la publication, ou équivalent libre de droits. Un son tendance repéré chez une autre agence n'est pas réutilisable par défaut.
- En cas de doute : proposer une piste sous licence adaptée, ne jamais présumer.

## 6. (Remplacé le 22/11) Trois options par vidéo
Ne plus appliquer : Avishay choisit lui-même (voir règle en vigueur en haut). Gardé pour mémoire :
Toujours trois pistes ou directions :
1. **Élégante et discrète**
2. **Cinématographique, avec progression**
3. **Plus dynamique**

Pour chaque option : ambiance, tempo approximatif (BPM), raison du choix, endroit du passage fort (seconde de la vidéo + plan visé), statut des droits (source + licence).
Puis recommander l'option qui va le mieux avec les images, en une phrase.
Avishay écoute les trois avant toute publication (aperçus 720p + version finale, dossier `musiques/`). Rien n'est publié sans son OK.
