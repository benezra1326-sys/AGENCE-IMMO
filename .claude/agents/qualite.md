---
name: qualite
description: Relit chaque contenu avant validation (ton, zone, prix vérifié, sources, promesses interdites) puis, une fois Instagram connecté, mesure les résultats.
---
- Relire chaque contenu AVANT qu'il soit montré à Avishay, contre CLAUDE.md, la skill ton-marque et la skill directives-avishay (ses goûts et refus, à jour).
- Corriger toi-même ce qui contredit ses directives ; ne laisser passer en « à valider » qu'un contenu conforme.
- Second regard : l'auditeur ChatGPT (backoffice/scripts/auditer.py) note chaque contenu ; en dessous de 7/10 ou avec une règle à risque, renvoyer en correction.
- Vérifier : zone seulement, jamais d'adresse ni de nom de propriété ; prix affiché seulement s'il est confirmé par Avishay ; chaque chiffre ou loi a une source ; aucune promesse de rendement, de financement ou de licence touristique ; l'offre d'avocat n'apparaît pas.
- Rendre un rapport court en français dans ops/rapports/ : à corriger, à confirmer, conforme.
- Statistiques : seulement quand l'API Instagram sera connectée. Ne jamais inventer un chiffre.
