# Pilotage PDV — Plateforme web décisionnelle

Projet de fin d'études — Bachelor Data & Business Intelligence (Nexa Digital School)
Titre visé : Chef de projet web (RNCP40857)
Auteur : Mohammed OUAHHABI

---

<<<<<<< HEAD

## 1. Présentation

=======

## 🔗 Accès à l'application en ligne

|                  |                                                   |
| ---------------- | ------------------------------------------------- |
| **URL publique** | **https://pilotage-pdv.onrender.com**             |
| **Hébergement**  | Render (offre gratuite) + base PostgreSQL managée |

### Comptes de démonstration

Mot de passe commun : **`motdepasse123`**

| Rôle                              | E-mail                        | Tableau de bord | Analyse | **Back-office** |
| --------------------------------- | ----------------------------- | :-------------: | :-----: | :-------------: |
| **Manager** (accès admin complet) | **`manager@pdv-nanterre.fr`** |       ✅        |   ✅    |       ✅        |
| Assistant manager                 | `adjoint@pdv-nanterre.fr`     |       ✅        |   ✅    |       ✅        |
| Premier équipier                  | `premier@pdv-nanterre.fr`     |       ✅        |   ✅    |       ❌        |
| Équipier                          | `equipier@pdv-nanterre.fr`    |       ✅        |   ❌    |       ❌        |

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
| `ventes_demo_juillet.csv`       | Import conforme — 186 lignes intégrées                           |
| `ventes_sale.csv`               | Contrôles qualité — 25 lues, 14 intégrées, **11 rejetées**       |
| `ventes_colonnes_exotiques.csv` | Correspondance de colonnes (noms différents, séparateur `;`)     |
| _le même fichier deux fois_     | **Idempotence** — 0 intégrées, N ignorées, indicateurs inchangés |

---

## 1. Stack technique

> > > > > > > bffea1f9a4d9862aa16ff945ed39d94eef93fe27

**Pilotage PDV** est une application web décisionnelle destinée au pilotage de la performance d'un point de vente (cas d'application : Domino's Pizza, point de vente de Chatou). Elle consolide les données de commandes et de ventes via un pipeline de fiabilisation, puis les restitue aux responsables dans une interface exploitable au quotidien : tableau de bord d'indicateurs, analyse des ventes, alertes et prévision d'affluence.

**Application déployée (URL publique) :** https://pilotage-pdv.onrender.com

> Remarque : l'application est hébergée sur une offre gratuite. Après une période d'inactivité, la première ouverture peut nécessiter un court délai de réveil (quelques dizaines de secondes).

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

## 2 bis. Contenu de l'archive livrée

| Élément                           | Description                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------- |
| `README.md`                       | Ce document : URL publique, accès back-office, installation, déploiement        |
| `app/`                            | Code source de l'application (modèles, services, blueprints, templates, CSS/JS) |
| `migrations/`                     | Migrations de schéma (Flask-Migrate / Alembic)                                  |
| `scripts/`                        | Jeu de démonstration, amorçage au déploiement, export SQL                       |
| `tests/`                          | 50 tests automatisés (pytest)                                                   |
| `sample_data/`                    | Fichiers CSV pour démontrer le pipeline                                         |
| `docs/`                           | Rédactionnel technique + `captures/` : 5 captures d'exécution                   |
| **`dump.sql`**                    | **Export SQL complet de la base** (schéma + données de démonstration)           |
| `requirements.txt`, `runtime.txt` | Dépendances et version de Python                                                |
| `render.yaml`, `Procfile`         | Configuration de déploiement (Render, gunicorn)                                 |
| `.env.example`                    | Modèle de configuration d'environnement                                         |
| `pytest.ini`                      | Configuration des tests                                                         |

---

## 3. Structure du projet

```
.
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Modèles de données (7 tables)
│   ├── blueprints/          # Modules : auth, dashboard, ventes, admin, imports, legal
│   ├── services/            # Logique métier : kpi, pipeline, alertes, prevision
│   └── templates/           # Gabarits Jinja2 (5 écrans + partials)
├── migrations/              # Migrations de base (Flask-Migrate)
├── scripts/                 # seed.py (données de démo), bootstrap.py, generer_dump.sh
├── tests/                   # Suite de tests pytest (43 tests)
├── render.yaml              # Configuration de déploiement (infrastructure as code)
├── Procfile                 # Commande de démarrage
├── runtime.txt              # Version de Python (3.12.5)
├── requirements.txt         # Dépendances Python
├── .env.example             # Modèle de variables d'environnement
└── dump.sql                 # Export SQL de la base de données
```

---

## 4. Installation et lancement en local

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

---

## 5. Comptes de démonstration

Ces comptes sont créés automatiquement par le chargement des données de démonstration (`python -m scripts.seed`).

**Mot de passe commun :** `motdepasse123`

| E-mail                   | Rôle              | Accès                                             |
| ------------------------ | ----------------- | ------------------------------------------------- |
| manager@pdv-nanterre.fr  | Manager           | Complet (dashboard, analyse, back-office, import) |
| adjoint@pdv-nanterre.fr  | Assistant manager | Complet                                           |
| premier@pdv-nanterre.fr  | Premier équipier  | Dashboard + analyse (lecture)                     |
| equipier@pdv-nanterre.fr | Équipier          | Dashboard (lecture)                               |

### Créer un compte administrateur (Manager) manuellement

```bash
flask creer-admin --email vous@example.com --nom "Votre Nom"
```

---

## 6. Tests

La suite de tests (43 tests) couvre les indicateurs, le pipeline d'import, les accès par rôle, l'administration et la couche décision.

```bash
pytest
```

---

## 7. Import de données (pipeline)

L'écran « Import de données » (réservé au manager et à l'assistant) permet de charger un fichier CSV de ventes. Le pipeline exécute, de façon visible, une série de contrôles qualité (doublons, valeurs manquantes, formats de date, quantités et montants invalides) avant d'intégrer les seules lignes valides.

- **Format attendu :** fichier CSV avec les colonnes date, produit, quantité, montant.
- **Colonnes non reconnues :** si les intitulés diffèrent, un écran de correspondance permet d'associer manuellement les colonnes.

Des jeux de données de test sont fournis pour illustrer les trois cas (fichier propre, fichier avec erreurs, fichier aux colonnes non standard).

---

## 8. Déploiement

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

## 9. Compatibilité

Application web responsive, compatible avec les navigateurs récents (Chrome, Firefox, Edge, Safari, Brave), sur ordinateur et smartphone. Connexion sécurisée en HTTPS une fois déployée.

---

## 10. Sécurité et conformité

- Mots de passe hachés (jamais stockés en clair).
- Gestion des rôles et protection des accès par décorateurs.
- Protection CSRF sur les formulaires, sessions sécurisées.
- Conformité RGPD : bandeau cookies, mentions légales, conditions d'utilisation, gestion des comptes.
- Aucune donnée réelle de l'entreprise n'est utilisée : l'application fonctionne sur un jeu de données représentatif.
