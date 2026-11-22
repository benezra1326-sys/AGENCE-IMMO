# Applications mobiles

Deuxième activité pilotée par l'agent maître, séparée de l'immobilier : ses agents, ses tâches et son bot Telegram sont à part.
Le back-office l'affiche dans la rubrique **Apps**.

## Les agents Apps

| Agent | Prénom proposé | Rôle | Instructions |
| --- | --- | --- | --- |
| apps-coordination | Léa | Cheffe de projet : planning, répartition, fiche d'état, récap Apps du matin | `agents/apps-coordination.md` |
| apps-produit | Noah | Benchmark, fonctionnalités, cahier des charges | `agents/apps-produit.md` |
| apps-design | Inès | Parcours, maquettes, identité visuelle | `agents/apps-design.md` |
| apps-dev | Sacha | Code de l'app, base de données, intégrations | `agents/apps-dev.md` |
| apps-qualite | Elias | Tests, essais sur téléphone, sécurité et données personnelles | `agents/apps-qualite.md` |
| apps-publication | Maya | Fiches App Store et Google Play, suivi de validation | `agents/apps-publication.md` |

Comme pour l'immobilier, ces fichiers sont des **instructions**, pas des agents qui tournent seuls. Leur état réel est tenu dans `backoffice/registre/agents.json`.

## Agents au travail (un agent = une session Claude sur un chantier)

Les six rôles ci-dessus sont des rôles types. Le travail réel est fait par des **agents au travail** : chaque session Claude (fil du projet APPS) qui travaille sur un chantier d'une app. Plusieurs tournent en parallèle sur la même app. Le back-office les liste dans **Applications › Agents au travail**, groupés par projet, avec leur nombre, leur statut et leur avancement.

Source : la base de données du back-office en ligne (artifact `https://claude.ai/artifact/WXAtJuTozPUQxa79AKo8D5`), collection **`apps_agents`**, un document par agent. Chaque session écrit **sa propre fiche** avec l'outil `ArtifactData` :

- au démarrage : `set` sur `apps_agents/<projet>-<chantier>` (ex. `motek-logo`) ;
- à chaque étape : `update` des champs qui changent (`statut`, `avancement`, `fait`, `prochaine_etape`, `blocages`, `liens`, `maj_le`) ;
- à la fin : `statut: "termine"`, `avancement: 100`. On ne supprime pas une fiche : elle passe dans « terminés ».

```json
{
  "projet": "kapara",
  "nom": "Logo MOTEK",
  "role": "Une phrase : ce que fait cet agent.",
  "specialite": "apps-design",
  "statut": "en_cours | a_valider | en_pause | bloque | termine",
  "avancement": 60,
  "fait": "Dernière action, une ligne.",
  "prochaine_etape": "Ce qui vient ensuite.",
  "blocages": ["Ce qu'il faut à Avishay pour débloquer."],
  "liens": [{"libelle": "PR #18", "url": "https://github.com/…"}],
  "fil": "https://claude.ai/code/project/<projet>?thread=<id du fil>",
  "debut": "2026-11-22T18:58:00Z",
  "maj_le": "2026-11-22T19:20:00Z"
}
```

- `projet` = identifiant de la fiche d'état de l'app dans la collection `apps_fiches`. MOTEK garde l'identifiant historique **`kapara`** (le nom affiché vient de la fiche). `commun` = travail partagé entre les apps (back-office, outils).
- `specialite` = l'un des six rôles types ci-dessus.
- Une nouvelle app : créer sa fiche `apps_fiches/<id>`, puis ses agents avec `projet: "<id>"`. Rien à changer dans le code du back-office.
- Mêmes règles que la fiche d'état : français, pas de secret ni de donnée personnelle, liens `https://` uniquement.

## Comment une app remonte son avancement

Chaque app a un dossier `apps/<id>/` :

- `app.json` : où lire la fiche d'état dans le dépôt de l'app (`source.depot`, `source.chemin`) ;
- `statut.json` : fiche d'état de secours, écrite dans ce dépôt.

Le back-office lit les deux toutes les 5 minutes et garde **la fiche la plus récente** (champ `maj_le`). Il existe aussi une troisième voie, quand le serveur sera en ligne : `POST /api/apps/statut` avec l'en-tête `X-Jeton` égal à `BO_APPS_TOKEN` et la fiche en corps JSON.

Pour KAPARA, le fil qui construit l'app écrit `status/kapara.json` dans le dépôt KAPARA.

### Format de la fiche d'état

```json
{
  "id": "kapara",
  "nom": "KAPARA",
  "description": "Une phrase sur l'app.",
  "depot": "benezra1326-sys/KAPARA",
  "etape": "idee | benchmark | cadrage | design | developpement | tests | publication | en_ligne",
  "statut": "en_cours | en_pause | bloque | termine",
  "avancement": 0,
  "resume": "Deux ou trois phrases en français, pour Avishay.",
  "prochaine_etape": "Ce qui vient juste après.",
  "blocages": ["Ce qui empêche d'avancer, et ce qu'il faut à Avishay pour débloquer."],
  "agents": ["apps-coordination", "apps-dev"],
  "chantiers": [
    {"nom": "Squelette technique", "statut": "a_faire | en_cours | termine | bloque", "avancement": 30, "responsable": "apps-dev"}
  ],
  "liens": [{"libelle": "Dépôt GitHub", "url": "https://github.com/…"}],
  "historique": [{"quand": "2026-11-22T03:22:00Z", "texte": "Ce qui s'est passé."}],
  "maj_le": "2026-11-22T03:30:00Z"
}
```

Règles : tout en français, pas de secret ni de donnée personnelle, `maj_le` mis à jour à chaque changement (sinon la fiche est ignorée), liens en `https://` uniquement.

Les tâches des agents Apps suivent le format habituel (`ops/taches/<id>.json`) avec `"activite": "apps"` et un agent `apps-…`.

## Bot Telegram Apps

Un second bot, distinct de @Avishay_immo_bot, pour que les informations des apps ne se mélangent pas avec l'immobilier.
Il prévient quand une app change d'étape, de statut, d'avancement ou qu'un blocage apparaît, et envoie un récap Apps chaque matin.

Commandes : `/apps`, `/app kapara`, `/taches`, `/blocages`, `/recap`. Tout autre message devient une consigne pour Léa (cheffe de projet Apps).

Mise en service :

1. Dans Telegram, ouvre **@BotFather**, envoie `/newbot`, choisis un nom (par exemple « Avishay Apps ») et un identifiant finissant par `bot`.
2. BotFather donne un jeton. Ne le colle pas dans le chat : ajoute-le comme variable `APPS_TELEGRAM_BOT_TOKEN` dans les réglages (et dans `/etc/backoffice.env` sur le serveur).
3. Le bot est réservé à ton compte : il utilise le même identifiant que le bot Immobilier (`TELEGRAM_CHAT_ID`), ou `APPS_TELEGRAM_CHAT_ID` si tu veux un autre compte.
4. Tant que `BO_MODE_ENVOI` vaut `test`, les messages sont préparés et visibles dans le back-office, rien n'est envoyé.
