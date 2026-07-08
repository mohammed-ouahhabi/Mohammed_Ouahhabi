# Partie 2a — La brique data : pipeline, connecteurs et gouvernance

> Paragraphe destiné au dossier PDF (Partie 2 — conception et développement).
> À reformuler à ta voix ; les chiffres et noms de fichiers sont à adapter.

## 1. Rôle de la brique data dans la solution

La valeur de l'application ne vient pas seulement de son interface, mais de la
**fiabilité des indicateurs** qu'elle affiche. Or ces indicateurs sont calculés
à partir de fichiers de ventes hétérogènes, produits par des systèmes de caisse
différents selon les points de vente. La brique data a donc une mission précise :
**transformer une source brute et variable en un entrepôt normalisé et fiable**,
sur lequel les KPI peuvent être calculés sans risque.

Cette brique est implémentée en Python avec **pandas** pour le traitement et
**SQLAlchemy** pour le chargement, et se décompose en quatre étapes rendues
visibles à l'utilisateur (écran « Import de données »).

## 2. Le schéma de collecte : une cible stable, une source libre

Le point de conception central est la distinction entre la **source** et la
**cible**.

- La **cible** est le schéma de l'entrepôt : chaque ligne de vente doit fournir
  une `date`, un `produit`, une `quantité` et un `montant`. C'est le minimum
  nécessaire au calcul des KPI (chiffre d'affaires, panier moyen, top produits,
  pics horaires). Ce schéma est **stable** et non négociable.
- La **source** est le fichier réel envoyé par un magasin. Ses colonnes peuvent
  porter des noms différents (`date_commande`, `order_date`, `article`, `qte`,
  `prix`…), utiliser un séparateur différent (`,` ou `;`) ou un format de date
  différent. La source est donc **variable**.

Concevoir un pipeline robuste, c'est refuser de coupler ces deux niveaux. Une
première version exigeait des noms de colonnes exacts : elle ne fonctionnait que
pour un seul format d'export et cassait pour tous les autres magasins. La version
retenue introduit une **couche de correspondance (mapping)** entre la source et
la cible.

## 3. Le connecteur : une couche de correspondance (mapping)

Concrètement, l'ingestion d'un fichier se fait désormais en deux temps :

1. **Détection.** À la réception du fichier, le pipeline lit uniquement les
   en-têtes et un échantillon de lignes. Un **dictionnaire d'alias** associe
   automatiquement les colonnes reconnues aux champs cibles (par exemple
   `date_commande`, `orderdate` ou `horodatage` sont reconnus comme le champ
   `date`). La comparaison est faite après normalisation (suppression des
   accents, de la casse et des séparateurs), pour tolérer les variantes
   d'écriture.
2. **Correspondance confirmée.** L'utilisateur visualise un aperçu de son fichier
   et une proposition de correspondance pré-remplie. Il confirme ou ajuste
   l'association de chaque champ, puis lance le traitement. Les colonnes non
   reconnues automatiquement sont associées manuellement en un clic.

Cette approche est celle des outils d'ingestion professionnels (import de
catalogues, connecteurs SaaS) : elle rend la solution **indépendante du format
d'export** et donc réellement déployable sur l'ensemble d'un parc de magasins,
sans redéveloppement pour chaque nouvelle source.

## 4. La gouvernance : contrôles qualité et traçabilité

La donnée n'est jamais chargée telle quelle. Avant l'intégration, chaque ligne
passe une série de **contrôles qualité**, dont le résultat est affiché à
l'utilisateur (transparence) :

- **Valeurs manquantes** — une ligne sans date, produit, quantité ou montant est
  rejetée.
- **Cohérence de format** — les dates sont validées contre plusieurs formats
  connus ; une date impossible (par exemple un mois « 13 ») est rejetée.
- **Validité métier** — une quantité doit être un entier strictement positif, un
  montant un nombre positif (la virgule décimale est acceptée).
- **Doublons** — deux lignes strictement identiques (même date, produit,
  quantité, montant) sont dédupliquées.

Seules les lignes valides sont chargées dans l'entrepôt via l'ORM. Les lignes de
vente partageant le même horodatage sont regroupées en une **commande** (ticket),
et le montant total de la commande est recalculé à l'intégration.

Enfin, **chaque import est journalisé** dans la table `import_fichier` : nom du
fichier, utilisateur, date, nombre de lignes lues, nombre de lignes rejetées et
statut. Cette traçabilité permet d'auditer l'historique des chargements et de
suivre la qualité des sources dans le temps — un réflexe de gouvernance des
données indispensable dès qu'un pipeline alimente des indicateurs de décision.

## 5. Ce que cette conception démontre

- **Séparation source / cible** : le schéma d'entrepôt reste stable, la variété
  des sources est absorbée par une couche de mapping.
- **Contrôles qualité explicites** : la fiabilité des KPI est garantie *avant*
  affichage, et le rejet est mesuré, pas silencieux.
- **Traçabilité** : chaque chargement laisse une trace exploitable.

## 6. Limites et évolutions envisagées

- **Profils de source mémorisés** : à ce stade, la correspondance est confirmée à
  chaque import. Une évolution naturelle consiste à **mémoriser un profil de
  mapping par magasin / par source**, pour que les imports suivants soient
  entièrement automatiques — c'est la définition d'un véritable connecteur ETL.
- **Orchestration** : le traitement est aujourd'hui déclenché manuellement. Sur
  un parc de magasins, une **orchestration planifiée** (par exemple avec un
  ordonnanceur type Airflow) permettrait des imports récurrents et supervisés.
- **Traitement asynchrone** : pour de très gros volumes, déporter le traitement
  dans une file de tâches éviterait de bloquer la requête web.
