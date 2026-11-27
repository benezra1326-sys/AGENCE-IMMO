# Outils externes installés (18/11/2026)

| Outil | Source | Licence | Comment c'est installé |
| --- | --- | --- | --- |
| Ultracode | github.com/pablonax/ultracode-skill | MIT | Copie de `ultracode/` dans `.claude/skills/ultracode` (Markdown seul, aucun script) |
| Ponytail | github.com/DietrichGebert/ponytail | MIT | Copie des 4 skills (`ponytail`, `-audit`, `-review`, `-help`) seulement. Les hooks du plugin (journal des coûts, webhook optionnel) ne sont PAS installés. |
| HyperFrames (HeyGen) | github.com/heygen-com/hyperframes | Apache-2.0 | Plugin officiel déclaré dans `.claude/settings.json` (marketplace `hyperframes`). Claude Code propose de l'installer à l'ouverture du dépôt. Rendu vidéo : Node 22+, FFmpeg, Chrome sur la machine. |

Sur le Mac d'Avishay (pas dans le dépôt) : HyperFrames (CLI + plugin) et Graphify (github.com/safishamsi/graphify, MIT, paquet Python `graphifyy`, commande `/graphify` : transforme un dossier en carte de connaissances).

Non installés : OmniRoute (abandonné par Avishay le 18/11/2026), Agent Skills d'Anthropic (déjà actifs sur le compte claude.ai).

## Contenu animé (ajouté le 18/11/2026)

Tous gratuits, copiés tels quels (Markdown + petits scripts de rendu locaux), aucune clé ni abonnement requis.

| Skills | Source | Licence | Sert à |
| --- | --- | --- | --- |
| `remotion-best-practices`, `remotion-create`, `remotion-captions`, `remotion-render` | github.com/remotion-dev/skills (officiel) | Licence Remotion : gratuite pour un indépendant ou une société de 3 personnes max, payante au-delà | Vidéo animée faite en code (React) : promo, sous-titres animés, rendu MP4 |
| `remotion-motion-graphics` | github.com/haidrrrry/claude-remotion-skill | MIT | Règles de qualité « motion design » pour éviter l'effet « vidéo IA générique » |
| `short-form-video`, `caption-animation`, `countdown-video`, `lower-thirds` | github.com/iart-ai/tiktok-video-skills | MIT | Reels / TikTok / Shorts, sous-titres mot à mot, comptes à rebours, bandeaux nom |
| `text-message-animation` | github.com/iart-ai/text-message-video-skills | MIT | Histoires racontées en conversation SMS / WhatsApp animée (format mini-série) |
| `explainer-video`, `whiteboard-animation`, `diagram-animation`, `isometric-animation`, `wrapped-video` | github.com/iart-ai/explainer-video-skills | MIT | Vidéos explicatives, tableau blanc, schémas, petites villes en 3D isométrique, récap façon « Wrapped » |
| `kinetic-typography` | github.com/iart-ai/kinetic-typography-skills | MIT | Texte qui bouge au rythme de la voix ou de la musique |
| `chart-animation`, `animated-infographic`, `presentation-video` | github.com/iart-ai/data-animation-skills | MIT | Graphiques et chiffres animés |
| `talking-head-b-roll` | github.com/iart-ai/b-roll-skills | MIT | Ajoute des animations sur une vidéo face caméra, à partir de ce qui est dit (transcription locale whisper.cpp ; ElevenLabs seulement si une clé est ajoutée) |
| `animation-principles`, `motion-art-direction`, `color-motion`, `shot-composition`, `beat-sync-editing`, `logo-animation`, `motion-background`, `after-effects`, `remotion-video` | github.com/iart-ai/motion-design-skills | MIT | Bases du motion design : rythme, couleurs, cadrage, calage sur le tempo, logo animé, fonds animés |
| `map-animation` | github.com/iart-ai/map-animation-skills | MIT | Cartes animées façon reportage (zones qui se colorent, trajets, épingles, distances) |
| `javascript-animation` | github.com/iart-ai/javascript-animation-skills | MIT | Petits films dessinés entièrement en code (décors illustrés, plans, caméra), sans aucune image |

Non installé : `generative-illustration` (demande une clé payante OpenRouter, pas de licence) ; le service payant iArt (MCP avec clé API) que ces dépôts proposent ; Higgsfield et autres générateurs vidéo IA (payants, voir mémoire du 10/11/2026).
Rendu : Node 18+, Chrome/Playwright et FFmpeg (déjà dans le cloud ; FFmpeg sur le Mac en attente de l'accord d'Avishay).

## Montage vidéo (ajouté le 26/11/2026, demande d'Avishay)

| Outil | Source | Licence | Où c'est installé | Sert à |
| --- | --- | --- | --- | --- |
| FFmpeg Skill (42 outils) | github.com/kajisho5/ffmpeg-skill (plugin officiel v4.8.3) | MIT | Plugin déclaré dans `.claude/settings.json` (marketplace `ffmpeg-skill`) | Couper les silences, sous-titres (karaoké), passage en 9:16, son à -14 LUFS, exports Reels. Tout en local, sans clé. |
| claude-shorts | github.com/Ansub/claude-shorts (commit 99c4d95) | MIT | `.claude/skills/claude-shorts` | Un clip vertical brut → Short fini : coupe les blancs et ratés, sous-titres mot à mot, musique baissée sous la voix, titre. whisper.cpp local (modèle ~3 Go au premier `setup.sh`). |
| long-to-shorts | github.com/Ansub/long-to-shorts (commit 9546046) | MIT | `.claude/skills/long-to-shorts` | Une vidéo longue (interview, visite) → ~10 Shorts sous-titrés. Même moteur local. |
| Ghost Editor | github.com/kurbaitaev/ghost-editor | MIT | Sur le Mac seulement (`~/.claude/skills/ghost-editor`, 19 styles, Mac Apple silicon) | Face caméra brut → Reel : meilleures prises, sous-titres qui évitent le visage, animations, bruitages. Clé Gemini gratuite facultative (les images vérifiées partent chez Google) ; ElevenLabs facultatif. |
| OpenMontage | github.com/calesthio/OpenMontage | AGPL-3.0 (usage interne OK, ne pas redistribuer modifié sans publier le code) | Projet à part sur le Mac (`~/OpenMontage`), pas dans ce dépôt (165 Mo) | Décortique un Reel de référence (accroche, rythme, montage) et reprend la structure. Beaucoup de fournisseurs payants en option : n'utiliser que le chemin local et gratuit sans accord. |

Non installé : Higgsfield « Editorial Motion Graphics » (le « Xfield » de la vidéo, github.com/higgsfield-ai/skills, MIT) : les skills sont gratuites mais la génération passe par un compte Higgsfield payant (crédits). À installer seulement si Avishay valide un abonnement.

## n8n, automatisations (ajouté le 26/11/2026, demande d'Avishay)

| Skills | Source | Licence | Sert à |
| --- | --- | --- | --- |
| 15 skills `*-official` (`using-n8n-skills-official`, `n8n-workflow-lifecycle-official`, `n8n-agents-official`, `n8n-ai-nodes-official`, `n8n-error-handling-official`, `n8n-credentials-and-security-official`, `n8n-data-tables-official`, `n8n-subworkflows-official`, `n8n-loops-official`, `n8n-expressions-official`, `n8n-code-nodes-official`, `n8n-node-configuration-official`, `n8n-binary-and-data-official`, `n8n-debugging-official`, `n8n-extending-mcp-official`) | github.com/n8n-io/skills v1.3.0 (commit 626f50f), éditeur officiel n8n | Apache-2.0 | Construire, tester et publier des workflows n8n proprement, avec le MCP officiel d'instance (connecteur « n8n » de claude.ai) |
| `n8n-workflow-patterns`, `n8n-self-hosting` | github.com/czlonkowski/n8n-skills v1.38.0 (commit ecdeca6), auteur de n8n-mcp | MIT (+ NOTICES Apache) | Modèles de workflows éprouvés ; installer n8n sur un petit serveur (Docker + Caddy, HTTPS) |

Choix : skills seulement. Non installés : les hooks des deux dépôts (scripts qui s'exécutent à chaque session) ; les autres skills czlonkowski, écrits pour son MCP à lui (`api.n8n-mcp.com`, service tiers hébergé) qui doublonne avec le MCP officiel ; le plugin « n8n Knowledge Base » (hooks + base tierce).
MCP : connecteur officiel « n8n » de claude.ai, à brancher sur l'instance d'Avishay (Settings → Instance-level MCP, n8n 2.2+). Le plugin officiel `n8n-skills@n8n-io` pourra être ajouté à `.claude/settings.json` quand l'adresse de l'instance existera.
Règles : aucun workflow n8n ne publie, n'envoie ni ne dépense sans l'OK d'Avishay (étape d'approbation obligatoire) ; pas de DM ni d'email à froid ; pas de robot LinkedIn.

## Les 5 packs « top 1 % » (ajoutés le 27/11/2026, demande d'Avishay)

Tous gratuits, licence MIT, copiés depuis le dépôt GitHub officiel de chaque auteur (Markdown seul, aucun hook).

| Pack | Source | Où c'est installé | Sert à (immo) |
| --- | --- | --- | --- |
| Skills d'ingénierie de Matt Pocock (dont `grill-me` / `grilling`, `tdd`, `diagnosing-bugs`, `to-spec`…) | github.com/mattpocock/skills v1.3.2 (commit 6f7f783) | Plugin officiel déclaré dans `.claude/settings.json` (`mattpocock-skills@claude-plugins-official`), pas de copie pour éviter les doublons et garder les mises à jour | Back-office, n8n, applis : `grill-me` interroge Avishay avant de construire quelque chose |
| `apple-design` (Emil Kowalski) | github.com/emilkowalski/skills (commit 64eb3de) | `.claude/skills/apple-design` | Interfaces propres et sobres : back-office, futures pages de biens |
| `humanizer` (Siqi Chen) | github.com/blader/humanizer v4.0.0 (commit a32f244), basé sur la page Wikipédia « Signs of AI writing » | `.claude/skills/humanizer` | Passe finale sur légendes, scripts, réponses DM, messages LinkedIn préparés |
| Motion Graphics Skill Pack (Charlie Hills) : 15 skills (`brand-intake`, `motion-brief-writer`, `motion-prompt-writer`, `motion-effects`, `animated-chart`, `milestone-reveal`, `launch-video`, `reference-to-motion`, `title-sequence-3d`, `newsletter-promo`, `model-showdown`, `loop-cover`, `apple-launch-film`, `reel-export`, `vox-explainer`) | github.com/charlie947/motion-graphics-skills (commit 229022e) | `.claude/skills/<nom>` (dossiers `assets/` 13 Mo et `prompts/` non copiés) | Vidéos entièrement en code (13 skills à l'origine, 15 aujourd'hui). Le moteur de rendu est HyperFrames, déjà installé (plugin). Utile : `reel-export`, `animated-chart`, `reference-to-motion`, `loop-cover` |
| Marketing Skills (Corey Haines) : 52 des 53 skills (SEO, copywriting, pubs, emails, CRO, réseaux sociaux…) | github.com/coreyhaines31/marketingskills (commit 2bf95ed) | `.claude/skills/<nom>` (dossiers `evals/` et `tools/` non copiés) | `copywriting`, `copy-editing`, `social`, `ad-creative`, `content-strategy`, `lead-magnets`, `marketing-psychology` pour les accroches, légendes et CTA |

Non installé : `cold-email` (Corey Haines) : la prospection par email à froid est interdite (LSSI art. 21, règle 2 du CLAUDE.md).
Les autres skills de ces packs restent soumis au CLAUDE.md et à `directives-avishay` : ton premium sans humour, aucune promesse de rendement / plus-value / financement / licence, aucun nom ni adresse de bien, aucun prix non vérifié, aucun pourcentage de commission, rien publié, envoyé ni dépensé sans l'OK d'Avishay. `sms`, `prospecting`, `popups` ou les intégrations payantes citées dans les skills ne s'utilisent qu'avec son accord. En cas de conflit, le CLAUDE.md gagne.

### Deuxième lot du 27/11/2026 (demande d'Avishay)

| Skill | Source | Licence | Sert à |
| --- | --- | --- | --- |
| `content-strategy`, `seo-audit`, `ai-seo`, `pricing` | déjà dans le pack Corey Haines ci-dessus | MIT | Planning éditorial, SEO du futur site, visibilité dans ChatGPT / Perplexity |
| `caveman` | github.com/JuliusBrussee/caveman (commit e74a11c), skill seul | Apache-2.0 | Réponses ultra-courtes pour économiser des tokens. Jamais pour les contenus publics (ton premium). Le plugin, ses hooks, son proxy et sa télémétrie ne sont PAS installés. |
| `anti-ai-slop-writing` | github.com/jalaalrd/anti-ai-slop-writing (commit 63255f9) | MIT (README) | Second filtre anti « texte d'IA », en complément de `humanizer`. Choisi parmi plusieurs skills du même nom : c'est le plus simple (Markdown seul). |
| `minimalist-ui` | github.com/Leonxlnx/taste-skill-classics (commit 5e08c93) | MIT | Interfaces sobres façon Notion / Linear (back-office). Se lance seulement quand on l'appelle par son nom. |
| `ui-ux-pro-max` | github.com/nextlevelbuilder/ui-ux-pro-max-skill (commit 11ca2b3) | MIT | Base de styles, palettes, polices et règles UX, avec un petit moteur de recherche Python local |
| `web-design-guidelines` | github.com/vercel-labs/agent-skills (commit 5a37a63) | MIT | Relecture d'une interface : accessibilité, ergonomie, bonnes pratiques Vercel |
| `agent-browser` | github.com/vercel-labs/agent-browser (commit 3f43a2a) | Apache-2.0 | Pilote un navigateur. Le skill est une porte d'entrée : il faut l'outil gratuit `npm i -g agent-browser` sur la machine. Jamais sur LinkedIn ni Instagram avec le compte d'Avishay (règles 3 et 4). |
| `find-skills` | github.com/vercel-labs/skills (commit e7fd0e9) | MIT | Cherche d'autres skills sur skills.sh. Toute nouvelle installation reste soumise à l'accord d'Avishay. |
| `video-lens` | github.com/kar2phi/video-lens (commit fa14db0) | MIT | Lien YouTube → rapport résumé (veille sur les agences et créateurs immo). Scripts Python locaux. |
| `video-use` | github.com/browser-use/video-use (commit 43cfc56) | MIT | Montage vidéo par conversation (coupes, étalonnage, sous-titres). Demande une clé ElevenLabs (transcription Scribe) : consomme les crédits de son abonnement ElevenLabs existant, à utiliser seulement avec son accord. |

### « Motion graphics » (27/11/2026, demande d'Avishay)

| Skills | Source | Licence | Sert à |
| --- | --- | --- | --- |
| `motion-broll`, `object-separation`, `explainer-high-energy`, `explainer-default`, `explainer-engaging`, `sound-effects` | github.com/Barty-Bart/motion-graphics (commit 3d83d98) | MIT | Animations calées sur la voix dans une vidéo face caméra, détourage d'une personne sur un nouveau fond (en local), petites vidéos promo, bruitages calés sur le rythme |

Choisi parce que le dépôt s'appelle exactement « motion-graphics » et qu'il est gratuit. Non retenu : Higgsfield « Editorial Motion Graphics » (génération payante). Le cours Skool cité dans le README est payant et n'est pas nécessaire. Sons : seulement des sources libres de droits ou que possède Avishay (Epidemic, Artlist = abonnements payants, pas sans son accord).
