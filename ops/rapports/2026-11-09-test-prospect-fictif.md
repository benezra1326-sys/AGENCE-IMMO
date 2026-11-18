# Test du parcours prospect fictif

Exécuté le 09/11/2026 10:54 UTC, en mode test (aucun envoi, aucune donnée réelle).

Résultat : **réussi** (13/13 contrôles).

| Contrôle | Résultat |
| --- | --- |
| 2 tâches du dépôt importées, réimport sans doublon | OK |
| Résultats attendus à chaque message | OK |
| Une seule fiche prospect | OK |
| Historique : 4 messages (le doublon est ignoré) | OK |
| Alertes de nouvelle demande : 1 Telegram + 1 email | OK |
| Pas de nouvelle alerte pour les échanges suivants | OK |
| Demande d'appel remontée tout de suite (Telegram + email) | OK |
| Deuxième demande d'appel : pas d'alerte en double | OK |
| Email adressé à avi@levygoldman.com | OK |
| Mode test : rien n'est envoyé | OK |
| Telegram : 3 réponses à Avishay, compte inconnu ignoré | OK |
| Telegram : le prospect fictif apparaît dans /prospects | OK |
| Récap du matin préparé (Telegram + email) | OK |

## Fiche obtenue

- P-e072fef4 – Camille Fictive [fictif] – source formulaire, FR, langue fr
- Budget 2.5 M€, zone Nueva Andalucía, projet residence_secondaire, statut appel_demande

## Alertes préparées (non envoyées)

### nouveau_prospect – telegram

```
[TEST - prospect fictif] Nouvelle demande – Camille Fictive (formulaire)
Fiche : P-e072fef4
Source : formulaire | Langue : fr | Pays : FR
Budget : 2.5 M€ | Zone : Nueva Andalucía | Projet : residence_secondaire
Message : « Bonjour, nous cherchons une résidence secondaire à Nueva Andalucía, budget 2,5 M€, plutôt une villa avec vue golf. »
Action : qualification en cours ; rien n'a été envoyé au prospect.
```

### nouveau_prospect – email → avi@levygoldman.com

```
[TEST - prospect fictif] Nouvelle demande – Camille Fictive (formulaire)
Fiche : P-e072fef4
Source : formulaire | Langue : fr | Pays : FR
Budget : 2.5 M€ | Zone : Nueva Andalucía | Projet : residence_secondaire
Message : « Bonjour, nous cherchons une résidence secondaire à Nueva Andalucía, budget 2,5 M€, plutôt une villa avec vue golf. »
Action : qualification en cours ; rien n'a été envoyé au prospect.
```

### appel_demande – telegram

```
[TEST - prospect fictif] APPEL DEMANDÉ – Camille Fictive
Fiche : P-e072fef4
Source : formulaire | Langue : fr | Pays : FR
Budget : 2.5 M€ | Zone : Nueva Andalucía | Projet : residence_secondaire
Message : « Bonjour, pouvez-vous m'appeler demain vers 10 h ? »
Action : rappeler dès que possible.
```

### appel_demande – email → avi@levygoldman.com

```
[TEST - prospect fictif] APPEL DEMANDÉ – Camille Fictive
Fiche : P-e072fef4
Source : formulaire | Langue : fr | Pays : FR
Budget : 2.5 M€ | Zone : Nueva Andalucía | Projet : residence_secondaire
Message : « Bonjour, pouvez-vous m'appeler demain vers 10 h ? »
Action : rappeler dès que possible.
```

## Récap du matin généré

```
Récap du 09/11/2026
(mode test : aucune alerte n'est réellement envoyée)

Productions (24 h) : 3
• Récap du matin 2026-11-09 (coordination)
• Test du parcours avec un prospect fictif (fiche, historique, anti-doublon, alertes préparées) (acheteurs)
• Back-office V1 : tableau de bord, modèle de tâches, bot Telegram, alertes (mode test) (coordination)

À valider : 0
Publications : 0 (publication automatique non activée)

Conversations (24 h) : 4 messages
Prospects nouveaux : 1
• Camille Fictive [fictif], budget 2.5 M€ – APPEL DEMANDÉ

Prospection B2B : 5 partenaires en liste, 0 contacté (envoi LinkedIn manuel par toi)

Tâches :
0 en attente, 0 en cours, 3 terminées, 0 en échec, 0 bloquées

Blocages :
• Connexions manquantes : Bot Telegram, Envoi d'emails d'alerte vers avi@levygoldman.com, Serveur (exécution Mac éteint), API Claude (modèles côté serveur), Stockage des médias lourds, Google Agenda

Coûts (24 h) : 0.00 €
Pubs : non activées
```
