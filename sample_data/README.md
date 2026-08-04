# Jeux de données de démonstration

Ces fichiers servent à rejouer, à l'identique, les scénarios d'import décrits
dans le dossier. Ils sont à charger depuis **Import de données** (compte Manager
ou Assistant), dans l'ordre du tableau : les trois premiers illustrent chacun un
cas, le quatrième démontre l'idempotence.

| # | Fichier | Ce qu'il démontre | Résultat attendu |
|---|---|---|---|
| 1 | `ventes_demo_juillet.csv` | Un import conforme. Colonnes standard, séparateur `,`, une colonne `mode_paiement` facultative reconnue automatiquement. | **186 lues · 186 intégrées · 0 rejetée** |
| 2 | `ventes_sale.csv` | Les contrôles qualité. Le fichier porte volontairement cinq familles d'anomalies. Aucun rejet n'est silencieux : chacun est motivé à l'écran. | **25 lues · 14 intégrées · 11 rejetées** |
| 3 | `ventes_colonnes_exotiques.csv` | Le découplage source / cible. Séparateur `;`, intitulés non standard : `horodatage`, `libelle_article`, `nb`, `total_ttc`, `reglement`. | **20 lues · 20 intégrées · 0 rejetée** |
| 4 | `ventes_demo_juillet.csv` *(à nouveau)* | **L'idempotence.** L'empreinte du fichier est reconnue, l'import est bloqué ; en forçant, aucune ligne n'est réinsérée. | **186 lues · 0 intégrée · 186 ignorées** — indicateurs inchangés |

---

## 1. Le fichier conforme — `ventes_demo_juillet.csv`

186 lignes de ventes du 1er au 14 juillet 2026, colonnes
`date, produit, quantite, montant, mode_paiement`.

Les valeurs de `mode_paiement` y sont écrites **« CB »**, là où le jeu de
démonstration écrit « Carte ». La normalisation des valeurs les ramène à un
libellé unique : sans elle, le même moyen de paiement apparaîtrait deux fois
dans le graphique de répartition.

## 2. Le fichier dégradé — `ventes_sale.csv`

Un fichier tel qu'on en reçoit réellement : 25 lignes, dont 11 inexploitables.

| Anomalie | Occurrences |
|---|---:|
| Valeur manquante | 3 |
| Doublon interne | 1 |
| Format de date invalide *(dont la mention littérale « hier »)* | 3 |
| Quantité invalide | 2 |
| Montant invalide | 2 |
| **Total rejeté** | **11** |

Ce fichier ne porte **pas** de colonne de mode de paiement : c'est le cas normal
d'un champ facultatif absent, qui ne déclenche aucune erreur.

## 3. Les colonnes non standard — `ventes_colonnes_exotiques.csv`

Le même magasin, un autre logiciel de caisse. `horodatage` et `nb` sont
reconnus automatiquement par le dictionnaire d'alias ; `libelle_article` et
`total_ttc` doivent être associés **à la main** sur l'écran de correspondance.

Ce fichier fait apparaître un produit absent du catalogue, **Salade César** :
il est créé à la volée, avec un prix déduit de la ligne (montant ÷ quantité) et
la catégorie « À qualifier », qui signale l'arbitrage restant.

---

`ventes_dominos_T1_2026.csv` est le **jeu de données de volume réel** :
12 234 lignes de ventes du 1er janvier au 31 mars 2026
(colonnes `date_heure, nom_pizza, quantite, prix_total, taille, categorie`).

Résultat de l'import :

| Indicateur | Valeur |
|---|---|
| Lignes lues | 12 234 |
| Lignes intégrées | 12 233 |
| Lignes rejetées | 1 (doublon strict — voir ci-dessous) |
| Commandes créées | 5 370 |
| Produits distincts | 32 |
| Pic d'activité | 12 h |
| Durée de traitement | ≈ 5 s |

> **Le doublon détecté est un cas limite intéressant à connaître.** Le ticket du
> 16/02/2026 à 18:15:02 contient **deux lignes strictement identiques**
> (« Steak and Cheese XL », 20,99 €) : un client a commandé deux fois le même
> article, enregistré en deux lignes de quantité 1 plutôt qu'en une ligne de
> quantité 2. Le contrôle qualité les considère comme un doublon et n'en retient
> qu'une. C'est une limite assumée de la règle actuelle : elle protège contre la
> duplication accidentelle, mais ne sait pas distinguer une répétition légitime
> au sein d'un même ticket.

---

## Anomalies volontaires du jeu de démonstration

Le jeu généré par `scripts/seed.py` n'est pas parfaitement régulier : deux
anomalies y sont **injectées délibérément**, afin que les règles de la couche
décision aient quelque chose à détecter. Un jeu lisse ne déclencherait aucune
alerte, et la fonctionnalité serait invisible à la démonstration.

| Anomalie | Où | Ce qu'elle déclenche |
|---|---|---|
| Journée à 45 % du régime normal | 3 jours avant le dernier jour | alerte **Chute de CA** (niveau critique) |
| Végétarienne remplacée à 85 % par Margherita | 12 derniers jours | alerte **Produit en décrochage** |

Le jeu s'arrête **la veille** du jour d'exécution, jamais sur la journée en
cours : une journée tronquée s'effondrerait sur la courbe d'évolution et
fausserait toute comparaison avec les journées entières qui la précèdent.

La graine aléatoire est fixe (`random.seed(42)`) : deux exécutions le même jour
produisent exactement le même jeu.
