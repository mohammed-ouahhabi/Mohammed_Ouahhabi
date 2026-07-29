# Prompt — Mise à jour du rapport de PFE (rapport + cahier des charges)

> **Mode d'emploi.** Copie-colle tout ce document dans ta discussion de rédaction,
> en y joignant ton fichier `PFE_rapport_VALIDE_2.docx`. Il est autonome : aucun
> autre fichier n'est nécessaire.

---

## Contexte

Tu m'aides à mettre à jour le rapport de mon projet de fin d'études (Bachelor
Data & Business Intelligence, titre visé « Chef de projet web », RNCP40857).

Le rapport ci-joint est **abouti** : environ 17 000 mots, structure complète
(Partie 1 — analyse des besoins, Partie 2 — conception et développement,
conclusion, quatre annexes dont un compte-rendu d'entretien). **Il ne s'agit pas
de le réécrire.**

Entre sa rédaction et aujourd'hui, l'application a évolué : cinq fonctionnalités
ont été développées, un écran a été ajouté, et un nom de point de vente a été
harmonisé. Le document doit refléter l'application réellement livrée, car le jury
manipulera celle-ci pendant la soutenance : tout écart entre le rapport et l'écran
serait relevé.

L'application est une plateforme web décisionnelle de pilotage d'un point de vente
Domino's (cas d'application : magasin de Chatou). Stack : Python/Flask,
SQLAlchemy, Flask-Migrate, Flask-Login, pandas, gabarits Jinja2 + Chart.js,
SQLite en développement et PostgreSQL en production, déployée sur Render.

## Règles à respecter

1. **Modifications additives.** N'enlève rien, ne renumérote rien, ne restructure
   pas. On insère des paragraphes dans des sections existantes.
2. **Conserve mon style.** Le rapport est écrit dans un registre sobre,
   professionnel, à la première personne quand il s'agit de mes choix. Les textes
   que je fournis ci-dessous sont rédigés dans ce registre : intègre-les tels
   quels ou ajuste-les à la marge, sans les rallonger.
3. **Pas de chiffres figés inutiles.** Le rapport évite délibérément d'annoncer un
   nombre de tests ou de lignes de code, ce qui le protège du vieillissement.
   Conserve cette prudence, sauf pour les chiffres que je fournis explicitement.
4. **Vérifie la cohérence** : quand une modification touche un décompte (nombre
   d'écrans, par exemple), répercute-la partout où ce décompte apparaît.
5. À la fin, **liste les sections modifiées** pour que je puisse relire ciblé.

---

# Les six modifications à apporter

## 1. § 10.7 — Ajouter l'idempotence des imports *(le plus important)*

La section « La gouvernance : contrôles qualité et traçabilité » liste les
contrôles, dont : *« Doublons — deux lignes strictement identiques sont
dédupliquées. »* Cette formulation est **incomplète** : elle ne décrit que le
dédoublonnage à l'intérieur d'un fichier.

**Insérer après la liste des contrôles :**

> **L'idempotence : un import rejouable sans fausser les indicateurs.**
> Un contrôle qualité ligne à ligne ne suffit pas : il dédoublonne au sein d'un
> fichier, mais rien n'empêche de réimporter deux fois le même export — et de
> doubler mécaniquement le chiffre d'affaires. Le pipeline garantit donc
> l'idempotence entre imports, par deux couches complémentaires.
>
> La première agit au niveau du fichier : une empreinte SHA-256 de son contenu est
> calculée et journalisée. Si un import réussi porte déjà la même empreinte,
> l'interface avertit l'utilisateur et bloque la réintégration par défaut, une
> option explicite permettant de poursuivre en connaissance de cause.
>
> La seconde, plus robuste, agit au niveau de la ligne : chaque ligne reçoit une
> clé déterministe dérivée de ses données métier — date, produit normalisé,
> quantité, montant — soumise à une contrainte d'unicité en base. À l'intégration,
> une ligne dont la clé existe déjà est ignorée, jamais réinsérée. Cette couche
> couvre aussi le recouvrement partiel, c'est-à-dire un fichier mêlant des lignes
> déjà connues et des lignes nouvelles.
>
> Conformément au principe de rejet mesuré et non silencieux, ces lignes ignorées
> ne disparaissent pas : elles sont comptées séparément des lignes rejetées,
> affichées dans le récapitulatif d'import et conservées dans le journal.
> Réimporter un fichier connu affiche explicitement « lignes lues : N,
> intégrées : 0, ignorées : N », et les indicateurs restent inchangés.

**Puis, en fin de § 10.7, ajouter cette limite assumée** (point d'honnêteté qui
renforce la crédibilité de la démarche) :

> La règle de dédoublonnage a toutefois une limite assumée. Sur le jeu de données
> trimestriel, un ticket comportait deux lignes strictement identiques — deux fois
> le même article au même instant. Le contrôle les traite comme un doublon et n'en
> retient qu'une, alors qu'il s'agit d'un achat légitime de deux exemplaires. La
> règle protège contre la duplication accidentelle, mais ne sait pas la distinguer
> d'une répétition volontaire au sein d'un même ticket. L'évolution consisterait à
> indexer la clé d'idempotence par rang d'occurrence.

## 2. § 16.3 — Illustrer la gestion des correctifs

La section décrit la méthode de correction sans l'illustrer. **Ajouter :**

> À titre d'illustration, un défaut de fiabilité a été identifié en exploitation :
> réimporter un fichier déjà traité réinsérait les ventes et gonflait le chiffre
> d'affaires. Le correctif — la double couche d'idempotence décrite au § 10.7 — a
> été développé localement, couvert par des tests dédiés (réimport à l'identique,
> recouvrement partiel, journalisation des lignes ignorées), validé par la suite
> de tests complète, puis déployé. Une action d'administration réservée au manager
> permet par ailleurs de repartir d'un jeu de données propre.
>
> Un second incident, survenu uniquement en production, mérite d'être rapporté.
> L'import se déroule en deux temps : le fichier est d'abord analysé pour proposer
> une correspondance de colonnes, puis traité une fois celle-ci confirmée. Il doit
> donc être conservé entre deux requêtes. La première version l'écrivait sur le
> disque local — ce qui fonctionne en développement, mais s'est révélé fragile une
> fois déployé : sur un hébergement de type conteneur, le système de fichiers est
> éphémère. Un redéploiement ou une mise en veille de l'instance efface le
> fichier, et l'utilisateur se voyait répondre que son dépôt était introuvable au
> moment de valider. Le fichier est désormais conservé en base de données le temps
> du traitement, la base étant le seul stockage réellement persistant de
> l'application ; le dépôt est supprimé dès le traitement terminé, et purgé au bout
> d'une heure en cas d'abandon. Cet incident illustre une différence structurante
> entre développement et production : ce qui est acquis localement — la
> persistance du disque — ne l'est pas nécessairement une fois déployé.

## 3. § 10.6 — Ajouter la recomposition de l'horodatage

Dans « Le connecteur : une couche de correspondance », **ajouter :**

> **Recomposition de l'horodatage.** Certains exports de caisse séparent la date et
> l'heure en deux colonnes distinctes. Le connecteur accepte donc une colonne
> « heure » facultative et recompose l'horodatage complet avant l'analyse. L'enjeu
> n'est pas cosmétique : les lignes étant regroupées en commandes par horodatage,
> une date sans heure agrégerait toutes les ventes d'une journée en une seule
> commande — faussant le nombre de commandes, le panier moyen et les pics horaires.
> Deux garde-fous encadrent la règle : si la colonne date porte déjà une heure,
> elle fait foi, afin d'éviter toute double heure ; si l'heure est absente ou
> illisible sur une ligne, la date seule est conservée, car l'heure est une
> précision et non une condition de validité.

## 4. § 13.9 — Ajouter la tenue en charge sur volume réel

La section « Les mesures de performance » ne mentionne aucun test de charge.
C'est une faiblesse : le jury peut demander « et sur un volume réel ? ».
**Ajouter :**

> **Tenue en charge.** Le pipeline a été éprouvé sur un export trimestriel de
> 12 234 lignes couvrant janvier à mars 2026, produisant 5 370 commandes et
> 32 produits distincts. Le traitement complet — lecture, contrôles qualité,
> intégration — s'exécute en environ cinq secondes.
>
> Cette mesure a d'ailleurs conduit à une optimisation. Une première version
> traitait le même fichier en onze secondes. L'analyse a montré que le coût ne
> venait pas du parcours ligne à ligne des contrôles qualité, inférieur à une
> seconde, mais de l'intégration : une écriture intermédiaire par commande — soit
> plus de cinq mille — et une requête produit par ligne. Les produits sont
> désormais résolus en une seule passe, et les objets créés via les relations de
> l'ORM, sans écriture intermédiaire. Le temps a été divisé par deux, à logique de
> contrôle qualité strictement inchangée.

**Annexe 3 — Jeux de données de test** : ajouter un quatrième jeu.

> **Jeu 4 — Fichier de volume réel.** Export trimestriel de 12 234 lignes.
> Objectif : vérifier la tenue en charge du pipeline et la justesse des
> indicateurs sur un volume représentatif d'une exploitation réelle.

## 5. Cahier des charges (§ 9.2) et Partie 2 — Le sixième écran

⚠️ **Le § 9.2 « Les fonctionnalités détaillées » ouvre sur « cinq écrans ».
L'application en compte désormais six.**

**a) Remplacer « cinq écrans » par « six écrans »**, et ajouter après l'écran 5 :

> **Écran 6 — Opportunités promotionnelles (front-office).** Prolongement de
> l'analyse des ventes : l'écran ne se contente pas de restituer le passé, il
> propose des actions commerciales chiffrées, organisées selon trois questions —
> quand agir (créneaux horaires dont le chiffre d'affaires décroche nettement),
> quoi pousser (produits dont la part de chiffre d'affaires est en retrait) et
> quelles formules créer (produits fréquemment achetés ensemble). Chaque
> proposition s'accompagne des chiffres qui la fondent. L'accès est aligné sur
> celui de l'analyse des ventes.

**b) Décrire la brique en Partie 2**, aux côtés des alertes et de la prévision :

> **Des écarts aux actions.** Une troisième brique décisionnelle prolonge les
> alertes et la prévision. Là où les premières signalent, celle-ci propose : des
> actions commerciales chiffrées, déduites des ventes déjà en base. Trois analyses
> la composent. Les créneaux en retrait identifient les heures dont le chiffre
> d'affaires est nettement inférieur à la moyenne horaire, en estimant le manque à
> gagner correspondant. Les produits en retrait signalent ceux dont la part de
> chiffre d'affaires reste sous la part moyenne malgré un volume de ventes
> significatif. Les associations de produits relèvent enfin les paires les plus
> souvent achetées dans une même commande, en comparant le panier moyen de ces
> commandes au panier global — une association qui fait monter le ticket est une
> candidate naturelle à une formule.
>
> Comme la prévision, cette brique repose sur des règles explicites et non sur un
> apprentissage automatique. Ce choix est assumé : une recommandation qu'un
> responsable ne peut pas comprendre est une recommandation qu'il n'appliquera
> pas. C'est aussi ce qui rend chaque règle testable, avec des résultats connus
> d'avance. Deux graphiques rendent l'écart visible plutôt que seulement lisible —
> le chiffre d'affaires par heure et la part de chaque produit — avec dans les deux
> cas la moyenne tracée en repère.
>
> Les limites sont affichées à l'écran, et non passées sous silence : ces pistes
> signalent des écarts sans les expliquer — un créneau creux peut relever d'une
> fermeture, d'un effectif réduit ou d'une réalité de quartier. Elles se lisent
> comme un point de départ à confronter au terrain. Par ailleurs, l'application ne
> conservant aucun historique de promotions passées, elle ne peut pas mesurer
> l'effet d'une opération déjà menée : ce serait l'évolution la plus utile.

**c) Cohérence à vérifier.** Répercute le passage de cinq à six écrans partout où
le décompte apparaît. **Exception importante** : le § 11.3 « Les cinq écrans
maquettés » doit rester à cinq — les maquettes d'origine en comptaient bien cinq.
Précise simplement que le sixième écran est né d'une évolution postérieure au
maquettage. C'est un point favorable : il démontre une démarche itérative.

## 6. Harmonisation Nanterre → Chatou

Le rapport situe le cas d'application à **Chatou**, ce qui est correct et cohérent
avec le compte-rendu d'entretien en annexe. L'application affichait encore
« Nanterre » : **elle a été corrigée**, le point de vente et les comptes de
démonstration sont désormais à Chatou. Vérifie simplement qu'aucune occurrence de
« Nanterre » ne subsiste dans le document.

---

## Annexe 2 — Captures à remplacer

Les captures de l'annexe 2 doivent être remplacées : elles montrent l'ancien nom
du point de vente. Six captures à jour sont disponibles :

| Fichier | Écran |
|---|---|
| `01_import_fichier_conforme.png` | Import réussi — 186 lignes intégrées |
| `02_import_avec_anomalies.png` | Contrôles qualité — 25 lues, 14 intégrées, 11 rejetées |
| `03_correspondance_colonnes.png` | Correspondance des colonnes, avant validation |
| `04_tableau_de_bord_alertes.png` | Tableau de bord avec le bandeau « À surveiller » |
| `05_analyse_prevision_paiements.png` | Analyse : prévision d'affluence et modes de paiement |
| `06_opportunites.png` | **Nouveau** — Opportunités promotionnelles |

Ajoute une entrée pour la sixième capture dans le texte de l'annexe.

---

## Ce que j'attends en retour

1. Le rapport mis à jour, au même format, **sans perte de mise en forme**.
2. La **liste des sections modifiées**, pour une relecture ciblée.
3. Le signalement de toute **incohérence résiduelle** que tu repérerais entre les
   différentes parties du document.
