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

## 3. Les opportunités promotionnelles — de l'alerte à l'action

Les deux premières briques signalent : l'une ce qui a dévié, l'autre ce qui
s'annonce. La troisième va un cran plus loin : elle propose **des actions
commerciales chiffrées**, organisées selon trois questions que se pose un
responsable de point de vente.

| Question | Analyse | Règle |
|---|---|---|
| **Quand** agir ? | Créneaux en retrait | un créneau dont le CA est inférieur à 60 % de la moyenne horaire, sur un volume significatif |
| **Quoi** pousser ? | Produits en retrait | un produit vendu au moins dix fois dont la part de CA est inférieure à 60 % de la part moyenne |
| **Comment** ? | Produits associés | les paires de produits les plus souvent achetées dans une même commande |

Chaque recommandation est accompagnée des chiffres qui la fondent : le manque à
gagner estimé pour un créneau, la part de chiffre d'affaires pour un produit, le
panier moyen des commandes concernées pour une association — comparé au panier
global, afin de distinguer les associations qui font réellement monter le ticket.

Deux graphiques rendent l'écart visible plutôt que seulement lisible : le
chiffre d'affaires par heure et la part de chaque produit, avec dans les deux cas
la moyenne tracée en repère et les éléments en retrait signalés.

**Aucun apprentissage automatique là non plus.** Chaque règle s'énonce en une
phrase et se vérifie à la main. C'est un choix assumé : une recommandation qu'un
responsable ne peut pas comprendre est une recommandation qu'il n'appliquera pas.
C'est aussi ce qui rend la brique testable — chaque règle est couverte par des
tests aux résultats connus d'avance.

**Limites explicitées à l'écran.** Ces pistes signalent des écarts, elles ne les
expliquent pas : un créneau creux peut relever d'une fermeture, d'un effectif
réduit ou d'une réalité de quartier. Elles se lisent comme un point de départ à
confronter au terrain. Par ailleurs, l'application ne dispose d'aucun historique
de promotions passées : elle ne peut donc pas mesurer l'effet d'une opération
déjà menée. Ce serait l'évolution la plus utile — enregistrer les promotions et
comparer les périodes.

## 4. Ce que cette couche démontre

- La plateforme passe du **constat** (reporting) à l'**aide à la décision**.
- Les deux briques sont **explicables** : des seuils clairs pour les alertes, une
  moyenne pour la prévision. À l'oral, chaque chiffre affiché peut être justifié.

> Dépendance à connaître : la prévision par créneau et l'alerte « pic horaire »
> supposent des données **horodatées à l'heure**. Si la source ne fournit qu'une
> granularité journalière, ces deux éléments se replient naturellement sur une
> maille au jour (prévision par jour de semaine), sans changer la méthode.
