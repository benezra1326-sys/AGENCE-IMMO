# Sauvegarde complète du projet AGENCE IMMO, 22 novembre 2026

Faite le 22/11/2026 (heure de Paris, vers 4 h). Elle contient tout ce qui a été produit dans le projet depuis le 30/10/2026.

## Ce que contient la sauvegarde

| Fichier | Contenu |
| --- | --- |
| `depot-AGENCE-IMMO-2026-11-22.bundle` | Le dépôt GitHub entier : les 9 branches, tout l'historique. Se restaure avec `git clone depot-AGENCE-IMMO-2026-11-22.bundle AGENCE-IMMO`. |
| `dossier-partage-2026-11-22.tar.gz` | Tout le dossier partagé du projet : contenus (vidéos, carrousels), médias des biens, musiques, voix, fichier clients, audit, prospection, démos d'outils, fichiers envoyés. S'ouvre en double-cliquant sur Mac. |
| `backoffice-page-2026-11-22.html` | La page du back-office telle qu'elle est en ligne (lien : https://claude.ai/artifact/WXAtJuTozPUQxa79AKo8D5). |
| `backoffice-base/` | Les données du back-office : vos décisions sur chaque contenu, vos consignes à Victor, le calendrier de publication (28 posts), les avis des auditeurs, les chiffres des réseaux. |
| `inventaire-fichiers.txt` | La liste de tous les fichiers de l'archive avec leur taille. |

Aucun mot de passe ni clé API n'est dans cette sauvegarde (vérifié par une recherche automatique). Les clés (OpenAI, ElevenLabs) restent uniquement dans les réglages de l'environnement Claude.

**Attention, données personnelles :** l'archive contient le fichier clients Levy & Goldman (994 contacts). Gardez-la sur votre Mac ou votre disque, ne la partagez pas. Le fichier clients n'est pas dans le dépôt GitHub (vérifié sur toutes les branches).

## Inventaire : ce qui a été fait

### Le « cerveau » (dépôt GitHub)
- **Instructions de l'agent maître** (`CLAUDE.md`) : rôle, cibles, règles non négociables (mode validation, pas de cold email, LinkedIn manuel).
- **9 sous-agents** : montage, contenu, voix, fiches-biens, veille-marché, pubs, leads, rappels, prospection.
- **Skills métier** : cibles, ton de marque, qualifier un lead, objections, prospection LinkedIn, musique des Reels, Reel à partir de photos.
- **Skills outils** : Ultracode, Ponytail, HyperFrames, 29 skills d'animation (Remotion, typographie animée, cartes, etc.).
- **Back-office (code serveur)** : application Python avec bot Telegram, leads, commissions, alertes, récap du matin, auditeur. Pas encore en ligne (attend le serveur à ~30 €/mois).
- **Outils de production** : montage des Reels, calage sur le tempo, rendu des carrousels et animations.
- **Biens** : registre AB-0001 (villa golf, Solvilla SV2342), AB-0002, AB-0004 (projet Benahavís).
- **Diffusion aux agents** : fiches produits WhatsApp (en attente de l'API Meta).
- **Prospection** : listes LinkedIn semaines 1 et 2.
- **Veille musique** : étude des Reels de 5 grosses agences de Marbella.

### Les contenus produits (dossier partagé, `agence-immo/contenus/`)
| Contenu | Où il en est |
| --- | --- |
| Reel villa golf (V2 à V6) | Validé par vous le 12/11 |
| Carrousel « Buying in Marbella » (V1 à V3) | Validé |
| Fiche WhatsApp AB-0002 | Validée |
| Animation « Holiday or rental » (V1 à V5) | Modification demandée |
| Posts LinkedIn semaine 1 | Modification demandée |
| Reel programme neuf New Golden Mile | Refusé, remplacé par le Reel projet de villa Benahavís (18/11) |
| Actus 1 et 2 (étrangers à Málaga, élections du 29/11) | Modification demandée (il manquait voix off et musique) |
| Actus 3 à 6, animation « vrai coût d'un achat à 1 M€ », guide de zone en carte animée | Préparés le 18/11, pas encore validés |
| Reel Aloha 40 (premier Reel) | Brouillon, nom du bien à ne jamais montrer |

### Autres éléments du dossier partagé
- **Médias des biens** (514 Mo) et **musiques** (837 Mo, pistes libres de droits proposées).
- **Voix** : essais de voix off.
- **Fichier clients** : base de 994 contacts (consentement email à « non » pour tous).
- **Audit** : copies de chaque contenu envoyées aux auditeurs (Codex et Antoine) et leurs avis.
- **Prospection** : lots de partenaires du 11/11 et du 16/11.
- **Démos d'outils** : carte Graphify, coffre Obsidian, démo HyperFrames.
- **Applications, chaîne IA** : notes de départ, projets en pause.

## Ce qui n'est pas dans la sauvegarde
- Les vidéos Solvilla de Dropbox (elles restent chez Solvilla).
- Les fichiers sur votre Mac (VoiceStudio, voix « Avi Voice »).
- Les comptes en ligne (Instagram, Buffer, vidIQ) : rien n'y est publié pour l'instant.
- La base Supabase : elle n'existe pas encore (aucun projet Supabase sur le compte).
