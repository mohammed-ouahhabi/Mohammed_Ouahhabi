# Jeux de données d'exemple

`ventes_exemple.csv` sert à démontrer le pipeline d'import.

Il contient volontairement **4 lignes à problème** pour illustrer les contrôles
qualité affichés à l'écran :

| Ligne | Anomalie détectée        |
|-------|--------------------------|
| `01/13/2026,Reine,...`            | format de date invalide (mois 13) |
| `2026-06-07 19:00,,1,13.90`       | valeur manquante (produit vide)   |
| `2026-06-08 20:30,Pepperoni,-2,…` | quantité invalide (négative)      |
| `2026-06-09 12:40,Calzone,1,abc`  | montant non numérique             |

Les 13 lignes valides sont intégrées, les 4 autres rejetées — le récapitulatif
affiche « 4 lignes rejetées ».

---

`ventes_magasin_lyon.csv` démontre la **compatibilité multi-magasins** : ses
colonnes portent des noms différents (`date_commande`, `article`, `qte`, `prix`)
et sont séparées par `;`. L'écran de correspondance les **auto-détecte** et les
associe au schéma cible — aucun redéveloppement nécessaire pour une nouvelle
source.

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
