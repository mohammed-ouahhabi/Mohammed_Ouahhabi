# Pilotage PDV — plateforme décisionnelle pour un point de vente

Application web de pilotage de la performance d'un point de vente (cas réel :
data analyst / data engineer chez Domino's Pizza). Elle consolide les données de
ventes via un **pipeline fiabilisé** et les restitue aux responsables du magasin
dans une interface exploitable au quotidien.

Projet de fin d'études — Bachelor « Chef de projet web » (RNCP40857), Nexa Digital School.

> **Confidentialité** : aucune donnée réelle d'entreprise n'est diffusée.
> L'application fonctionne sur un jeu de données représentatif reconstitué.

---

## 1. Stack technique

| Brique | Choix |
|---|---|
| Backend | **Flask** (Python) |
| ORM / migrations | **SQLAlchemy** + **Flask-Migrate** |
| Authentification | **Flask-Login** (sessions) |
| Rôles | **décorateurs maison** (champ `role` sur l'utilisateur) |
| Formulaires / sécurité | **Flask-WTF** (protection CSRF) |
| Pipeline de données | **pandas** |
| Front-office | **templates Jinja2** + **Chart.js** (embarqué, pas de CDN) |
| Base | **SQLite** en développement, **PostgreSQL** en production |
| Serveur prod | **gunicorn** (déploiement Render) |
| Tests | **pytest** |

La bascule SQLite → PostgreSQL se fait **sans changer le code** : seule la variable
d'environnement `DATABASE_URL` change (voir `app/config.py`).

---

## 2. Les 5 écrans

1. **Connexion** — authentification (Flask-Login).
2. **Tableau de bord** — KPI (CA, commandes, panier moyen, produits vendus),
   évolution du CA, top produits, pics d'activité par heure (Chart.js).
3. **Analyse des ventes** — ventes par période, filtres (mois / produit / catégorie),
   tableau détaillé par produit, export CSV.
4. **Administration** (back-office) — gestion des utilisateurs (CRUD) et des sources.
5. **Import de données** — upload CSV, pipeline pandas avec contrôles qualité
   **visibles**, chargement, récapitulatif.

### Rôles et accès (décorateurs de contrôle d'accès)

| Rôle | Tableau de bord | Analyse | Back-office / Import |
|---|:---:|:---:|:---:|
| Manager | ✅ | ✅ | ✅ |
| Assistant manager | ✅ | ✅ | ✅ |
| Premier équipier | ✅ | ✅ (lecture) | ❌ |
| Équipier | ✅ (lecture) | ❌ | ❌ |

---

## 3. Structure du projet

```
Mohammed_Ouahhabi/
├── app/
│   ├── __init__.py          # application factory + commandes CLI (creer-admin, seed)
│   ├── config.py            # configurations dev / prod / test (bascule SQLite/PostgreSQL)
│   ├── extensions.py        # db, migrate, login_manager, csrf
│   ├── models.py            # modèles SQLAlchemy (= schéma relationnel fourni)
│   ├── decorators.py        # role_requis(...) : contrôle d'accès par rôle
│   ├── forms.py             # formulaires Flask-WTF (CSRF)
│   ├── services/
│   │   ├── kpi.py           # calcul des indicateurs (CA, panier moyen, top produits…)
│   │   └── pipeline.py      # pipeline d'import CSV (pandas + contrôles qualité)
│   ├── blueprints/          # une route par écran (auth, dashboard, ventes, admin, imports, legal)
│   ├── templates/           # gabarits Jinja2 (reproduisent les maquettes)
│   └── static/              # CSS (design system), JS, Chart.js embarqué
├── migrations/              # migrations Flask-Migrate (Alembic)
├── scripts/
│   ├── seed.py              # jeu de données de démonstration
│   └── generer_dump.sh      # export SQL (dump) SQLite ou PostgreSQL
├── sample_data/             # CSV d'exemple pour tester le pipeline
├── tests/                   # tests pytest (KPI, pipeline, accès, back-office)
├── wsgi.py                  # point d'entrée (flask run / gunicorn)
├── requirements.txt
├── render.yaml              # déploiement Render (web + PostgreSQL)
└── Procfile
```

**Pour ajouter un écran** : créer un blueprint dans `app/blueprints/`, l'enregistrer
dans `app/__init__.py`, ajouter son template dans `app/templates/` et un lien dans
`app/templates/partials/sidebar.html`.

---

## 4. Installation et lancement (développement)

Prérequis : Python 3.11+.

```bash
# 1. Environnement virtuel
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

# 2. Dépendances
pip install -r requirements.txt

# 3. Variables d'environnement
cp .env.example .env               # puis éditez SECRET_KEY si besoin
export FLASK_APP=wsgi.py           # Windows : set FLASK_APP=wsgi.py

# 4. Base de données (SQLite) + migrations
flask db upgrade

# 5. Jeu de données de démonstration (comptes + ventes)
flask seed

# 6. Lancer l'application
flask run
```

Application disponible sur http://127.0.0.1:5000.

### Comptes de démonstration (créés par `flask seed`)

Mot de passe commun : `motdepasse123`

| E-mail | Rôle |
|---|---|
| `manager@pdv-nanterre.fr` | Manager |
| `adjoint@pdv-nanterre.fr` | Assistant manager |
| `premier@pdv-nanterre.fr` | Premier équipier |
| `equipier@pdv-nanterre.fr` | Équipier |

### Créer un compte administrateur (Manager) manuellement

```bash
flask creer-admin --email vous@example.com --nom "Votre Nom"
```

### Tester le pipeline d'import

Depuis un compte Manager/Assistant → **Import de données** → charger
`sample_data/ventes_exemple.csv` (contient volontairement 4 lignes invalides
pour illustrer les contrôles qualité).

---

## 5. Tests

```bash
pytest
```

Couvre : calculs KPI, pipeline (contrôles qualité + intégration), matrice
d'accès par rôle, CRUD back-office, gestion RGPD des comptes.

---

## 6. Déploiement (URL publique + PostgreSQL)

Le fichier `render.yaml` décrit l'infrastructure. Sur [Render](https://render.com) :

1. **New +** → **Blueprint**, pointez sur ce dépôt Git.
2. Render lit `render.yaml` et crée : une base **PostgreSQL** + un service web.
3. Au déploiement : installation des dépendances, `flask db upgrade` (migrations),
   puis démarrage via `gunicorn wsgi:app`.
4. Créez le premier compte admin depuis le shell Render :
   `flask creer-admin --email ... --nom ...` (et éventuellement `flask seed` pour la démo).

`SECRET_KEY` est générée automatiquement ; `DATABASE_URL` est injectée depuis la
base PostgreSQL — l'application bascule alors de SQLite à PostgreSQL sans
modification de code. Les cookies de session passent en `Secure` (HTTPS) en prod.

### Export SQL (dump) de la base

```bash
# SQLite (dev)
./scripts/generer_dump.sh                       # -> dump.sql

# PostgreSQL (prod)
DATABASE_URL=postgresql://... ./scripts/generer_dump.sh
```

---

## 7. Conformité (Bloc 4)

- **RGPD** : bandeau cookies (uniquement le cookie de session, strictement
  nécessaire), mentions légales, CGU, politique de confidentialité ; page
  « Mon compte » (droit de rectification et d'effacement).
- **Sécurité** : mots de passe **hachés** (Werkzeug), **CSRF** sur tous les
  formulaires, sessions Flask-Login (`HttpOnly`, `SameSite`, `Secure` en prod),
  routes protégées par les décorateurs de rôle.
- **Accessibilité** : HTML sémantique, `lang="fr"`, libellés de formulaire,
  attributs ARIA (`aria-current`, `aria-label`), lien d'évitement, focus visible,
  contrastes conformes, design **responsive** (mobile-first).
- **Tests** : unitaires (KPI, pipeline) et d'intégration (accès, back-office).

---

## 8. Choix techniques importants (à défendre)

- **Décorateurs de rôle maison** plutôt qu'une librairie de permissions : la
  logique tient en 15 lignes (`app/decorators.py`) et reste entièrement explicable.
- **Couche `services/`** séparée des vues : les calculs (KPI) et le pipeline sont
  isolés, donc testables sans passer par HTTP.
- **Chart.js embarqué** (dossier `static/vendor/`) plutôt que depuis un CDN :
  l'application fonctionne hors-ligne, utile pour une démonstration.
- **Regroupement des lignes en commandes par horodatage** dans le pipeline :
  sans identifiant de commande dans le CSV, l'instant d'achat est le meilleur
  regroupement (une ligne = un article, un horodatage = un ticket).
- **Colonne `mot_de_passe_hash`** ajoutée au modèle `utilisateur` : seule addition
  au schéma métier, indispensable à l'authentification (jamais de mot de passe en clair).

---

## 9. Limites et pistes d'amélioration

- Le « rafraîchissement » des sources dans le back-office renvoie vers l'import
  manuel : une synchronisation automatique (planifiée) serait une évolution.
- Les KPI sont calculés à la volée ; sur de très gros volumes, une pré-agrégation
  (table de synthèse) améliorerait les temps de réponse.
- Import synchrone : pour de très gros fichiers, un traitement asynchrone (file de
  tâches) éviterait de bloquer la requête.
- Gestion multi-points-de-vente présente dans le schéma mais l'interface est
  aujourd'hui centrée sur le PDV de l'utilisateur connecté.
