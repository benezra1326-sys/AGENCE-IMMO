# Back-office Avishay

Tableau de bord privé, bot Telegram, alertes prospects et suivi des tâches des trois activités
(Immobilier actif ; Applications et Réseaux « à configurer »).

Python 3.11+ et la bibliothèque standard uniquement : rien à installer, aucun abonnement requis pour l'essayer.

## Ce qui est fait et testé (9 novembre 2026)

- Modèle de tâches : responsable, statut, dates, source, résultat, fichiers, coût, raison d'échec ;
  clé unique contre les doublons ; nouvel essai automatique (2, 4, 8 min…) puis « échec » ; « bloquée » quand une connexion manque ; relance manuelle.
- Import des tâches écrites dans le dépôt (`ops/taches/<id>.json`) et des fiches biens (`data/biens/<ref>.json`), sans doublon.
- Demandes immobilières : fiche créée ou enrichie, historique, anti-doublon (même message, même email écrit autrement, même téléphone),
  alerte Telegram + email à la première demande, alerte immédiate et unique pour une demande d'appel.
- Bot Telegram réservé à un seul compte : consigne, état, tâches, contenus à valider (boutons Valider / Modifier), prospects, récap.
- Récap du matin (08:00 Madrid), un seul par jour.
- Tableau de bord lisible sur téléphone, protégé par mot de passe.

Tout tourne en **mode test** : les alertes sont préparées et visibles, rien n'est envoyé.

## Essayer en local

```bash
cd backoffice
python3 -m unittest discover -s tests -t .          # 21 tests
python3 -m scripts.test_prospect_fictif              # parcours prospect fictif complet
python3 -m app.service                               # http://127.0.0.1:8787
```

## Format d'une tâche écrite dans le dépôt

`ops/taches/<id>.json` : `id, activite, agent, titre, statut (en_attente|en_cours|terminee|echec|bloquee), source,
cree_le, maj_le, resultat, fichiers[], cout_eur, raison_echec` et, pour un contenu à valider,
`contenu: {titre, format, langue, statut, date_prevue, bien}`. Les médias lourds restent hors du dépôt.

## Mise en production

Voir `deploy/` (service systemd, Caddy pour HTTPS, `env.exemple`). Les secrets vont uniquement dans
`/etc/backoffice.env` sur le serveur, jamais dans le dépôt ni dans le chat.
