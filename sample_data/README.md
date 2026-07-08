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
