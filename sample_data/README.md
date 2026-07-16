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

`ventes_demo_juillet.csv` est un **jeu propre prêt à importer** : 186 lignes de
ventes valides sur deux semaines (1er–14 juillet 2026), regroupées en 93 tickets.
Il inclut la colonne facultative `mode_paiement` (CB, Espèces, Ticket resto),
auto-détectée elle aussi. À l'import : **0 ligne rejetée**, 186 lignes intégrées,
soit 2 561,30 € de chiffre d'affaires. Idéal pour une démo « qui marche du
premier coup ».

---

`ventes_magasin_lyon.csv` démontre la **compatibilité multi-magasins** : ses
colonnes portent des noms différents (`date_commande`, `article`, `qte`, `prix`)
et sont séparées par `;`. L'écran de correspondance les **auto-détecte** et les
associe au schéma cible — aucun redéveloppement nécessaire pour une nouvelle
source.
