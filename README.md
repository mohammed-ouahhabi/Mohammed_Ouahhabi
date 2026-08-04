# Pilotage PDV — Plateforme web décisionnelle

Projet de fin d'études — Bachelor Data & Business Intelligence (Nexa Digital School)
Titre visé : Chef de projet web (RNCP40857)
Auteur : Mohammed OUAHHABI

---

## 1. Présentation

**Pilotage PDV** est une application web décisionnelle destinée au pilotage de la performance d'un point de vente (cas d'application : Domino's Pizza, point de vente de Chatou). Elle consolide les données de commandes et de ventes via un pipeline de fiabilisation, puis les restitue aux responsables dans une interface exploitable au quotidien : tableau de bord d'indicateurs, analyse des ventes, alertes, prévision d'affluence et opportunités promotionnelles.

---

## 🔗 Accès à l'application en ligne

|                  |                                                   |
| ---------------- | ------------------------------------------------- |
| **URL publique** | **https://pilotage-pdv.onrender.com**             |
| **Hébergement**  | Render (offre gratuite) + base PostgreSQL managée |

### Comptes de démonstration

Mot de passe commun : **`motdepasse123`**

| Rôle                              | E-mail                      | Tableau de bord | Analyse | **Back-office** |
| --------------------------------- | --------------------------- | :-------------: | :-----: | :-------------: |
| **Manager** (accès admin complet) | **`manager@pdv-chatou.fr`** |       ✅        |   ✅    |       ✅        |
| Assistant manager                 | `adjoint@pdv-chatou.fr`     |       ✅        |   ✅    |       ✅        |
| Premier équipier                  | `premier@pdv-chatou.fr`     |       ✅        |   ✅    |       ❌        |
| Équipier                          | `equipier@pdv-chatou.fr`    |       ✅        |   ❌    |       ❌        |

➡️ **Pour accéder au back-office d'administration**, connectez-vous avec le compte
**Manager** ci-dessus, puis utilisez la section « Administration » de la barre
latérale : _Utilisateurs & sources_ (gestion des comptes) et _Import de données_
(pipeline). Le compte Manager donne également accès à la réinitialisation du jeu
de démonstration.

> ⏱️ **Première visite** : sur l'offre gratuite de Render, l'instance se met en
> veille après ~15 minutes d'inactivité. Le premier chargement peut donc prendre
> **30 à 60 secondes**, le temps du réveil. Les suivants sont immédiats.

### Pour tester le pipeline d'import en ligne

Depuis le compte Manager → **Import de données** → chargez l'un des fichiers du
dossier `sample_data/` :

| Fichier                         | Ce qu'il démontre                                                |
| ------------------------------- | ---------------------------------------------------------------- |
| `ventes_demo_juillet.csv`       | Import conforme — 186 lues, 186 intégrées, 0 rejetée             |
| `ventes_sale.csv`               | Contrôles qualité — 25 lues, 14 intégrées, **11 rejetées**       |
| `ventes_colonnes_exotiques.csv` | Correspondance de colonnes (noms différents, séparateur `;`)     |
| `ventes_dominos_T1_2026.csv`    | Volume réel — 12 234 lignes, 5 370 commandes (≈ 5 s de traitement) |
| _le même fichier deux fois_     | **Idempotence** — 0 intégrée, N ignorées, indicateurs inchangés  |

> L'ordre compte : chargez les fichiers dans l'ordre du tableau, puis rechargez
> le premier pour observer l'idempotence. Les captures de `docs/captures/` ont
> été produites exactement dans cette séquence, et les chiffres correspondants
> sont consignés dans `docs/fiche_de_verite.md`.

---

## 2. Stack technique

| Domaine                | Technologies                                    |
| ---------------------- | ----------------------------------------------- |
| Back-end               | Python, Flask                                   |
| Base de données (ORM)  | SQLAlchemy, Flask-Migrate                       |
| Authentification       | Flask-Login                                     |
| Traitement des données | pandas                                          |
| Front-end              | Gabarits Jinja2 (HTML/CSS/JS), Chart.js         |
| Base de données        | SQLite (développement), PostgreSQL (production) |
| Serveur de production  | Gunicorn                                        |
| Hébergement            | Render                                          |
| Tests                  | pytest                                          |
| Versionnement          | Git / GitHub                                    |

---

## 3. Contenu de l'archive livrée

| Élément                           | Description                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------- |
| `README.md`                       | Ce document : URL publique, accès back-office, installation, déploiement        |
| `app/`                            | Code source de l'application (modèles, services, blueprints, templates, CSS/JS) |
| `migrations/`                     | Migrations de schéma (Flask-Migrate / Alembic)                                  |
| `scripts/`                        | Jeu de démonstration, amorçage au déploiement, export SQL                       |
| `tests/`                          | 72 tests automatisés (pytest)                                                   |
| `sample_data/`                    | Fichiers CSV pour démontrer le pipeline                                         |
| `docs/`                           | Rédactionnel technique, `fiche_de_verite.md` + `captures/` : 8 captures d'exécution |
| **`dump.sql`**                    | **Export SQL complet de la base** (schéma + données de démonstration)           |
| `requirements.txt`, `runtime.txt` | Dépendances et version de Python                                                |
| `render.yaml`, `Procfile`         | Configuration de déploiement (Render, gunicorn)                                 |
| `.env.example`                    | Modèle de configuration d'environnement                                         |
| `pytest.ini`                      | Configuration des tests                                                         |

---

## 4. Les six écrans

| # | Écran                              | Ce qu'il apporte                                                             | Accès                               |
| - | ---------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------- |
| 1 | **Tableau de bord**                | 4 indicateurs, alertes en tête de page, évolution du CA, top produits, pics d'activité | tous les rôles                      |
| 2 | **Analyse des ventes**             | ventes par période, détail par produit, prévision d'affluence, modes de paiement, export CSV | manager, assistant, premier équipier |
| 3 | **Produits**                       | catalogue des produits vendus                                                | manager, assistant, premier équipier |
| 4 | **Opportunités promotionnelles**   | créneaux en retrait, produits en retrait, associations de produits           | manager, assistant, premier équipier |
| 5 | **Administration**                 | gestion des utilisateurs et des sources, réinitialisation du jeu de démonstration | manager, assistant                  |
| 6 | **Import de données**              | pipeline d'import et son suivi                                               | manager, assistant                  |

Les écrans 1, 2 et 4 forment une progression volontaire : le tableau de bord dit
**ce qui s'est passé**, les alertes **ce qui mérite attention**, les opportunités
**ce qu'on peut décider**.

---

## 5. Modèle de données

Huit tables : **sept tables métier**, plus une table technique.

| Table              | Rôle                                                                     |
| ------------------ | ------------------------------------------------------------------------ |
| `point_de_vente`   | le magasin piloté                                                        |
| `utilisateur`      | comptes, rôle et empreinte du mot de passe                               |
| `produit`          | catalogue                                                                |
| `commande`         | un ticket                                                                |
| `ligne_commande`   | une ligne de ticket — **seule source du chiffre d'affaires**             |
| `vente`            | l'encaissement associé (export Pulse), porte le mode de paiement         |
| `import_fichier`   | journal des imports : lignes lues, intégrées, ignorées, rejetées         |
| `import_temporaire`| _(technique)_ dépôt du fichier entre les deux étapes de l'import         |

> **L'invariant du modèle :** le chiffre d'affaires est calculé **exclusivement**
> à partir de `ligne_commande`. La table `vente` sert à l'analyse des
> encaissements ; elle n'intervient jamais dans le calcul du CA, ce qui interdit
> tout double comptage.

`import_temporaire` existe parce que le système de fichiers d'un hébergement en
conteneur est éphémère : conserver le fichier sur disque entre l'étape de
correspondance et l'étape de traitement exposait à un « fichier introuvable »
après une mise en veille.

---

## 6. Structure du projet

```
.
├── app/
│   ├── __init__.py          # Application factory + commandes CLI
│   ├── models.py            # Modèles de données (8 tables)
│   ├── decorators.py        # Contrôle d'accès par rôle
│   ├── forms.py             # Formulaires Flask-WTF (protection CSRF)
│   ├── blueprints/          # auth, dashboard, ventes, admin, imports, legal
│   ├── services/            # kpi, pipeline, alertes, prevision, opportunites
│   ├── static/              # CSS, JS, Chart.js servi en local (aucun CDN)
│   └── templates/           # Gabarits Jinja2 (6 écrans + partials + pages d'erreur)
├── migrations/              # Migrations de schéma (Flask-Migrate / Alembic)
├── scripts/
│   ├── seed.py              # Jeu de démonstration
│   ├── bootstrap.py         # Amorçage au déploiement (base vide uniquement)
│   ├── diagnostic.py        # Quelle base, quelle révision, quel schéma
│   ├── reinit_db.py         # Réinitialisation locale (développement uniquement)
│   └── generer_dump.sh      # Export SQL
├── tests/                   # Suite de tests pytest (72 tests, 10 fichiers)
├── sample_data/             # Jeux de données de démonstration + leur README
├── docs/                    # Rédactionnel, fiche de vérité, 8 captures d'exécution
├── render.yaml              # Configuration de déploiement (infrastructure as code)
├── Procfile                 # Commande de démarrage
├── runtime.txt              # Version de Python (3.12.5)
├── requirements.txt         # Dépendances Python
├── .env.example             # Modèle de variables d'environnement
└── dump.sql                 # Export SQL de la base de données
```

---

## 7. Installation et lancement en local

### Prérequis

- Python 3.12
- Git

### Étapes

```bash
# 1. Récupérer le projet
git clone <url-du-depot>
cd <dossier-du-projet>

# 2. Créer et activer un environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux

# 5. Créer la base de données (applique les migrations)
flask db upgrade

# 6. Charger les données de démonstration
python -m scripts.seed

# 7. Lancer l'application
flask run
```

L'application est alors accessible à l'adresse : http://127.0.0.1:5000

> ⚠️ **Après chaque récupération de code (`git pull`)**, relancez
> `flask db upgrade` avant de démarrer l'application. Si le schéma de la base a
> évolué et que les migrations ne sont pas appliquées, les écrans concernés
> affichent une page d'erreur explicite rappelant cette commande.

### En cas de problème avec la base locale

Deux utilitaires sont fournis :

```bash
# Diagnostic : quelle base est utilisée, à quelle révision, quel schéma
python -m scripts.diagnostic

# Réinitialisation complète (développement uniquement) :
# supprime la base locale, rejoue les migrations, recharge le jeu de démo
python -m scripts.reinit_db
```

`reinit_db` est une opération destructrice : il **refuse de s'exécuter** sur
autre chose qu'une base SQLite locale et demande une confirmation explicite.

Les migrations sont par ailleurs **défensives** : chaque table ou colonne n'est
créée que si elle est absente. Une base dont le registre de migrations s'est
désynchronisé du schéma réel — cas d'une base créée hors migrations — peut ainsi
rattraper son retard sans échouer sur un « table already exists ».

---

## 8. Comptes de démonstration

Ces comptes sont créés automatiquement par le chargement des données de démonstration (`python -m scripts.seed`).

**Mot de passe commun :** `motdepasse123`

| E-mail                    | Rôle              | Accès                                             |
| ------------------------- | ----------------- | ------------------------------------------------- |
| manager@pdv-chatou.fr     | Manager           | Complet (dashboard, analyse, back-office, import) |
| responsable@pdv-chatou.fr | Manager           | Complet                                           |
| adjoint@pdv-chatou.fr     | Assistant manager | Complet                                           |
| premier@pdv-chatou.fr     | Premier équipier  | Dashboard + analyse (lecture)                     |
| equipier@pdv-chatou.fr    | Équipier          | Dashboard (lecture)                               |

### Créer un compte administrateur (Manager) manuellement

```bash
flask creer-admin --email vous@example.com --nom "Votre Nom"

```

Le mot de passe est demandé de façon interactive, avec confirmation : il n'est
jamais passé sur la ligne de commande, où il resterait dans l'historique du
terminal.

---

## 9. Tests

La suite compte **72 tests** répartis en 10 fichiers. Elle couvre les indicateurs,
le pipeline d'import, la recomposition de l'horodatage, l'idempotence, les accès
par rôle, l'administration, la table `vente` et la couche décision.

```bash
pytest
```

---

## 10. Import de données (pipeline)

L'écran « Import de données » (réservé au manager et à l'assistant) charge un
fichier CSV de ventes en **deux étapes** : lecture des en-têtes et confirmation
de la correspondance, puis contrôles qualité et intégration.

### Le principe : source libre, cible stable

Les colonnes du fichier source peuvent porter **n'importe quel nom**. Un
dictionnaire d'alias les rapproche automatiquement du schéma cible, et un écran
de correspondance permet d'associer à la main celles qui n'ont pas été
reconnues. C'est cette couche qui rend la solution déployable sur un parc de
magasins équipés de logiciels de caisse différents, sans redéveloppement.

| Champ cible                     | Statut       |
| ------------------------------- | ------------ |
| date, produit, quantité, montant | obligatoires |
| heure, mode de paiement          | facultatifs  |

### Ce que le pipeline sait faire

- **Détection automatique du séparateur** (`,` ou `;`) et de l'encodage.
- **Plusieurs formats de date** acceptés (`AAAA-MM-JJ`, `JJ/MM/AAAA`, avec ou
  sans heure).
- **Recomposition de l'horodatage** lorsque la date et l'heure figurent dans
  **deux colonnes distinctes** — cas fréquent des exports de caisse.
- **Normalisation des valeurs de mode de paiement** : « CB », « carte
  bancaire », « TPE » sont ramenés à un libellé unique. Sans cela, le même moyen
  de paiement apparaîtrait plusieurs fois dans l'analyse. Une valeur inconnue est
  conservée telle quelle plutôt que perdue.
- **Contrôles qualité** rejetant une ligne : valeur manquante, doublon interne,
  format de date invalide, quantité ou montant invalide. **Chaque rejet est
  motivé et affiché** — jamais silencieux.
- **Produits inconnus créés à la volée**, avec un prix déduit de la ligne qui les
  a fait apparaître et la catégorie « À qualifier », qui signale l'arbitrage
  restant.

### L'idempotence : un import rejouable

Deux garde-fous, complémentaires :

1. **Au niveau du fichier** — son empreinte SHA-256 est enregistrée. Un fichier
   déjà traité est reconnu et l'import est **bloqué par défaut** ; l'utilisateur
   peut passer outre en connaissance de cause.
2. **Au niveau de la ligne** — chaque ligne porte une clé déterministe
   (date + produit normalisé + quantité + montant) sous contrainte d'unicité.
   Une ligne déjà présente n'est **jamais réinsérée**, même si elle provient d'un
   autre fichier.

Conséquence : recharger un export déjà intégré affiche **0 ligne intégrée, N
ignorées**, et les indicateurs restent strictement inchangés. C'est la
différence entre un pipeline de démonstration et un pipeline exploitable.

Les jeux de données de `sample_data/` illustrent chacun de ces cas ; leur
contenu est décrit dans `sample_data/README.md`.

---

## 11. Déploiement

Le déploiement est décrit dans le fichier `render.yaml` (infrastructure as code). Sur Render, la création d'un « Blueprint » à partir de ce fichier crée automatiquement :

- le service web (application Flask servie par Gunicorn) ;
- une base de données PostgreSQL managée.

Au démarrage, le service applique les migrations, amorce les données si la base est vide, puis lance l'application. La bascule de SQLite (développement) vers PostgreSQL (production) est automatique, via la variable d'environnement `DATABASE_URL` renseignée par l'hébergeur — sans modification du code.

### Générer l'export SQL (dump)

```bash
bash scripts/generer_dump.sh
```

Le fichier `dump.sql` permet de reconstituer la base de données à l'identique.

---

## 12. Compatibilité

Application web responsive, compatible avec les navigateurs récents (Chrome, Firefox, Edge, Safari, Brave), sur ordinateur et smartphone. Connexion sécurisée en HTTPS une fois déployée.

---

## 13. Sécurité et conformité

- Mots de passe hachés (jamais stockés en clair).
- Gestion des rôles et protection des accès par décorateurs.
- Protection CSRF sur les formulaires, sessions sécurisées.
- Conformité RGPD : bandeau cookies, mentions légales, conditions d'utilisation, gestion des comptes.
- Aucune donnée réelle de l'entreprise n'est utilisée : l'application fonctionne sur un jeu de données représentatif.
