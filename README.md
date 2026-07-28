# Pilotage PDV — Plateforme web décisionnelle

Projet de fin d'études — Bachelor Data & Business Intelligence (Nexa Digital School)
Titre visé : Chef de projet web (RNCP40857)
Auteur : Mohammed OUAHHABI

---

## 1. Présentation

**Pilotage PDV** est une application web décisionnelle destinée au pilotage de la performance d'un point de vente (cas d'application : Domino's Pizza, point de vente de Chatou). Elle consolide les données de commandes et de ventes via un pipeline de fiabilisation, puis les restitue aux responsables dans une interface exploitable au quotidien : tableau de bord d'indicateurs, analyse des ventes, alertes et prévision d'affluence.

**Application déployée (URL publique) :** https://pilotage-pdv.onrender.com

> Remarque : l'application est hébergée sur une offre gratuite. Après une période d'inactivité, la première ouverture peut nécessiter un court délai de réveil (quelques dizaines de secondes).

---

## 2. Stack technique

| Domaine | Technologies |
|---|---|
| Back-end | Python, Flask |
| Base de données (ORM) | SQLAlchemy, Flask-Migrate |
| Authentification | Flask-Login |
| Traitement des données | pandas |
| Front-end | Gabarits Jinja2 (HTML/CSS/JS), Chart.js |
| Base de données | SQLite (développement), PostgreSQL (production) |
| Serveur de production | Gunicorn |
| Hébergement | Render |
| Tests | pytest |
| Versionnement | Git / GitHub |

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

| E-mail | Rôle | Accès |
|---|---|---|
| manager@pdv-nanterre.fr | Manager | Complet (dashboard, analyse, back-office, import) |
| adjoint@pdv-nanterre.fr | Assistant manager | Complet |
| premier@pdv-nanterre.fr | Premier équipier | Dashboard + analyse (lecture) |
| equipier@pdv-nanterre.fr | Équipier | Dashboard (lecture) |

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