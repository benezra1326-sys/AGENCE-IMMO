# Outils externes installés (18/11/2026)

| Outil | Source | Licence | Comment c'est installé |
| --- | --- | --- | --- |
| Ultracode | github.com/pablonax/ultracode-skill | MIT | Copie de `ultracode/` dans `.claude/skills/ultracode` (Markdown seul, aucun script) |
| Ponytail | github.com/DietrichGebert/ponytail | MIT | Copie des 4 skills (`ponytail`, `-audit`, `-review`, `-help`) seulement. Les hooks du plugin (journal des coûts, webhook optionnel) ne sont PAS installés. |
| HyperFrames (HeyGen) | github.com/heygen-com/hyperframes | Apache-2.0 | Plugin officiel déclaré dans `.claude/settings.json` (marketplace `hyperframes`). Claude Code propose de l'installer à l'ouverture du dépôt. Rendu vidéo : Node 22+, FFmpeg, Chrome sur la machine. |

Non installés : Graphify (paquet Python `graphifyy` à installer sur le Mac), OmniRoute (passerelle qui redirige vers des comptes IA tiers, clés requises), Agent Skills d'Anthropic (déjà actifs sur le compte claude.ai).
