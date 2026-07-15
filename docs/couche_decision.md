# La couche « aide à la décision » (alertes & prévision)

> Paragraphe pour le dossier PDF. Ce qui distingue la plateforme d'un simple
> outil de reporting : elle ne se contente pas d'afficher le passé, elle aide à
> décider. Deux briques, en lecture seule au-dessus des données existantes
> (aucune nouvelle table, aucune migration).

## 1. Les alertes — « ce qui mérite attention »

Un service (`app/services/alertes.py`) parcourt les données du point de vente et
signale automatiquement les situations à surveiller, affichées dans un bandeau
« À surveiller » en haut du tableau de bord. Chaque alerte a un niveau
(`info` / `attention` / `critique`), un titre court et un message chiffré.

Trois règles, dont les seuils sont des constantes ajustables :

| Règle | Déclenchement | Niveau |
|---|---|---|
| **Produit en décrochage** | quantité vendue en baisse de plus de 30 % vs la période précédente (à volume significatif) | attention |
| **Chute de chiffre d'affaires** | journée dont le CA est > 25 % sous la moyenne du même jour de semaine (> 40 % : critique) | attention / critique |
| **Pic d'activité inhabituel** | créneau horaire dépassant de plus de 50 % sa moyenne habituelle | info |

Le chiffre d'affaires n'est jamais recalculé dans ce service : il réutilise les
fonctions de `services/kpi.py` (source unique de vérité = `ligne_commande`).

## 2. La prévision d'affluence — « regarder en avant »

Un service (`app/services/prevision.py`) estime l'affluence des 7 prochains jours,
par créneau horaire, pour aider au **staffing**. Le résultat est affiché sous
forme de graphique sur la page d'analyse des ventes.

**Méthode assumée : statistique simple, sans machine learning.** L'affluence
prévue d'un créneau (jour de la semaine × heure) est la **moyenne des commandes
observées sur ce même créneau dans l'historique** du point de vente.

En une phrase : *on estime chaque créneau par la moyenne des créneaux équivalents
passés.*

**Pourquoi pas de machine learning ?** C'est un choix de conception, pas une
limite : la méthode statistique est **robuste, transparente et explicable**, et
suffisante pour un besoin de staffing. Un modèle de ML (régression, séries
temporelles) est mentionné comme **évolution future** — il exigerait davantage de
données, un entraînement et une justification de sa complexité, sans garantie de
gain pour ce cas d'usage.

## 3. Ce que cette couche démontre

- La plateforme passe du **constat** (reporting) à l'**aide à la décision**.
- Les deux briques sont **explicables** : des seuils clairs pour les alertes, une
  moyenne pour la prévision. À l'oral, chaque chiffre affiché peut être justifié.

> Dépendance à connaître : la prévision par créneau et l'alerte « pic horaire »
> supposent des données **horodatées à l'heure**. Si la source ne fournit qu'une
> granularité journalière, ces deux éléments se replient naturellement sur une
> maille au jour (prévision par jour de semaine), sans changer la méthode.
