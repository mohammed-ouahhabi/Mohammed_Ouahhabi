# Fiche de vérité — session de capture du 4 août 2026

> **Ce document remplace tous les chiffres qui circulaient auparavant.** Il est
> établi *depuis la session qui a produit les captures de `docs/captures/`*, et
> non depuis le code ni de mémoire. Toute valeur écrite dans le rapport ou la
> présentation doit venir d'ici.
>
> **Méthode suivie**, dans cet ordre exact, sans rien réimporter entre deux :
> réinitialisation de la base → import conforme → import dégradé → colonnes
> exotiques → réimport du fichier conforme → capture des huit écrans.

---

## Les huit captures

| Fichier | Écran |
|---|---|
| `01_import_fichier_conforme.png` | Import d'un fichier conforme |
| `02_import_avec_anomalies.png` | Import d'un fichier dégradé, détail des rejets |
| `03_correspondance_colonnes.png` | Correspondance de colonnes (source exotique) |
| `04_reimport_idempotence.png` | **Réimport — idempotence** *(nouvelle)* |
| `05_tableau_de_bord_alertes.png` | Tableau de bord + bandeau d'alertes |
| `06_analyse_prevision_paiements.png` | Analyse des ventes, prévision, modes de paiement |
| `07_opportunites.png` | Opportunités promotionnelles |
| `08_produits.png` | Catalogue produits *(nouvelle)* |

---

## Le pipeline — les quatre imports de la session

Ces quatre lignes apparaissent **ensemble** dans le tableau « Derniers imports »
de la capture 04. C'est la meilleure preuve du dossier : toute la démonstration
du pipeline tient sur une seule image.

| Fichier | Lues | Intégrées | Ignorées | Rejetées |
|---|---:|---:|---:|---:|
| `ventes_demo_juillet.csv` | 186 | **186** | 0 | 0 |
| `ventes_sale.csv` | 25 | **14** | 0 | **11** |
| `ventes_colonnes_exotiques.csv` | 20 | **20** | 0 | 0 |
| `ventes_demo_juillet.csv` *(réimport)* | 186 | **0** | **186** | 0 |

Détail des 11 rejets : **3 valeurs manquantes · 1 doublon · 3 dates · 2 quantités · 2 montants**.

---

## Volumes en base après la session

| | |
|---|---:|
| Commandes | 3 357 |
| Lignes de commande | 6 663 |
| Ventes (table `vente`, source Pulse) | 3 357 |
| Produits au catalogue | 9 |

Le jeu de démonstration couvre **75 jours, jusqu'à la veille incluse** — jamais
la journée en cours, qui serait tronquée.

---

## Tableau de bord — 30 derniers jours

| Indicateur | Valeur | Variation |
|---|---:|---:|
| Chiffre d'affaires | **44 812,10 €** | −1 % |
| Commandes | **1 371** | +3 % |
| Panier moyen | **32,69 €** | −4 % |
| Produits vendus | **3 981** | stable |

## Alertes affichées

| Niveau | Alerte |
|---|---|
| **Critique** | Chute de CA le 31/07 — 858 €, soit −48 % sous la moyenne des vendredis récents (~1 652 €) |
| Attention | Produit en décrochage : Végétarienne — 211 ventes contre 333 sur la période précédente (−37 %) |
| Attention | Chute de CA le 02/08 — 1 386 €, soit −28 % sous la moyenne des dimanches récents (~1 914 €) |

> ⚠️ **Ces valeurs se déplacent à chaque réinitialisation** : le jeu est calé sur
> la date d'exécution. Dans la présentation, cite la **règle** (« un jour à plus
> de 40 % sous la moyenne de son jour de semaine »), pas le chiffre. Les deux
> anomalies qui déclenchent ces alertes sont **injectées volontairement** dans le
> jeu de démonstration, et documentées dans `sample_data/README.md`.

---

## Opportunités — 90 derniers jours

**Moyenne horaire : 9 438,29 € · seuil à 60 % : 5 662,97 €**
**6 créneaux sur 12 sont sous le seuil** — tous signalés en rouge sur le
graphique ; le détail retient les trois plus pénalisants.

| Créneau | CA | Écart | Manque à gagner |
|---|---:|---:|---:|
| 16 h – 17 h | 2 675,50 € | **−72 %** | 6 762,79 € |
| 15 h – 16 h | 2 820,30 € | −70 % | 6 617,99 € |
| 11 h – 12 h | 4 204,80 € | −55 % | 5 233,49 € |

Produits en retrait (part moyenne par produit : 11,1 %) :
**Salade César 0,1 % · Tiramisu 3,5 % · Boisson 33 cl 4,0 %**

Associations — panier moyen global **33,74 €** :

| Association | Commandes | Panier moyen | Écart |
|---|---:|---:|---:|
| Boisson 33 cl + Reine | 297 | 36,94 € | +3,20 € |
| Boisson 33 cl + Pepperoni | 253 | 39,95 € | +6,21 € |
| **Pepperoni + Reine** | 239 | 53,54 € | **+19,80 €** |

> **Le chiffre à mettre en avant reste l'écart de panier de Pepperoni + Reine.**
> Sa valeur exacte change à chaque réinitialisation ; sa formulation robuste est
> *« une association qui fait monter le ticket de près de vingt euros »*.

---

## Modes de paiement

| Mode | Encaissements |
|---|---:|
| Carte | 2 046 |
| Espèces | 951 |
| Ticket resto | 347 |

**Trois catégories, pas quatre.** Les fichiers importés écrivent « CB » là où le
jeu de démonstration écrit « Carte » : la normalisation des *valeurs*
(`normaliser_mode_paiement`) les ramène à un libellé unique. Sans elle, le même
moyen de paiement apparaîtrait deux fois dans le graphique.

*(13 encaissements sont sans mode de paiement : ils proviennent de
`ventes_sale.csv`, qui ne porte pas cette colonne. C'est le comportement attendu
d'un champ facultatif.)*

---

## Catalogue produits

| Produit | Catégorie | Prix |
|---|---|---:|
| Boisson 33cl | Boisson | 2,50 € |
| Tiramisu | Dessert | 4,90 € |
| 4 Fromages · Calzone · Margherita · Pepperoni · Reine · Végétarienne | Pizza | 15,90 / 14,50 / 11,90 / 14,90 / 13,90 / 13,50 € |
| **Salade César** | **À qualifier** | **8,90 €** |

Salade César n'existait pas au catalogue : elle a été **découverte à l'import**
du fichier aux colonnes exotiques. Son prix est déduit de la ligne qui l'a fait
apparaître (montant ÷ quantité) et sa catégorie signale explicitement qu'un
arbitrage humain reste à faire.

> **C'est un bon point à faire remarquer au jury** plutôt qu'à masquer : il
> montre qu'un import ouvert à n'importe quelle source crée des produits, et que
> l'application le signale au lieu de le dissimuler.

---

## Ce qui ne bouge jamais

Ces éléments sont structurels : ils ne dépendent d'aucune session.

- **8 tables** : `point_de_vente` · `utilisateur` · `produit` · `commande` ·
  `ligne_commande` · `vente` · `import_fichier` · `import_temporaire`
  *(les sept premières sont métier, la dernière est technique)*
- **6 écrans** : tableau de bord · analyse des ventes · produits · opportunités ·
  administration · import
- **4 rôles** : manager · assistant manager · premier équipier · équipier
- **Le CA est calculé exclusivement depuis `ligne_commande`.** La table `vente`
  ne participe jamais à ce calcul.
- **72 tests** automatisés (pytest).
- Point de vente : **Chatou (78)**.
- Aucun apprentissage automatique : toutes les règles sont déterministes et
  énonçables en une phrase.
