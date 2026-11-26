# n8n : options et premières automatisations IMMO (26/11/2026)

## Où faire tourner n8n
| Option | Coût | Pour | Contre |
| --- | --- | --- | --- |
| n8n Cloud Starter | 20 $/mois (annuel), 2 500 exécutions/mois | Rien à installer, MCP officiel prêt, mises à jour faites | Payant, plafond d'exécutions |
| n8n Cloud Pro | 50 $/mois (annuel), 10 000 exécutions/mois | Marge pour beaucoup de workflows | Plus cher |
| Auto-hébergé (Hetzner CX23, 2 vCPU / 4 Go, Allemagne/Finlande) | ~6 €/mois HT + nom de domaine (~1 €/mois) | Le moins cher, exécutions illimitées, données en UE | Serveur à entretenir (on s'en charge avec le skill `n8n-self-hosting`) |

Sources : n8n.io/pricing, hetzner.com/cloud/cost-optimized (lus le 26/11/2026).
Recommandation : auto-hébergé Hetzner (~7 €/mois, bien sous les ~30 €/mois prévus). Rien n'est souscrit sans l'OK d'Avishay.

## Premières automatisations (ordre proposé)
Règle commune : chaque workflow s'arrête sur une étape « À valider par Avishay » (Telegram ou back-office) avant toute publication, tout envoi ou toute dépense.

1. **Leads entrants → base commune** : formulaire du site / Meta Lead Ads / email entrant → fiche lead (nom, source, pays, langue, budget, zone, délai, projet, statut) → alerte Telegram en français. Réponse proposée en brouillon, envoyée par Avishay.
2. **Mots-clés en DM Instagram** (MARBELLA, ZONE, GUIDE) : uniquement sur DM entrant, via l'API officielle ; réponse préparée et validée avant mise en route.
3. **Récap du matin** (8 h, Madrid) : tâches de `ops/taches/`, leads, contenus à valider, coûts → message Telegram en français.
4. **Rapport du vendredi** : statistiques Instagram réelles (« non disponible » si absentes).
5. **Planning de contenu** : contenu validé dans le back-office → programmé dans Buffer / Meta à la date validée (jamais avant son OK).
6. **Rappels de visite** : J-1 et H-2 dans Google Agenda + relance post-visite préparée en brouillon.
7. **Veille marché** : flux sources officielles (INE, notariat, Junta) → résumé hebdo sourcé pour l'agent veille-marche.
8. **Prospection LinkedIn** : n8n prépare la liste du jour (≈15) et les messages dans le back-office ; Avishay envoie à la main. Aucun clic automatique.

Exclus : cold email, DM à froid, robot LinkedIn, publication sans OK.
