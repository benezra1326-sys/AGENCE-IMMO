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

Non installé : le service payant iArt (MCP avec clé API) que ces dépôts proposent ; Higgsfield et autres générateurs vidéo IA (payants, voir mémoire du 10/11/2026).
Rendu : Node 18+, Chrome/Playwright et FFmpeg (déjà dans le cloud ; FFmpeg sur le Mac en attente de l'accord d'Avishay).
