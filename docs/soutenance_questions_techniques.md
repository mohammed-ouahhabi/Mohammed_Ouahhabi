# Entretien technique — questions anticipées et réponses

> L'entretien dure 10 à 15 minutes. Le jury cherche moins la bonne réponse que la
> capacité à **justifier un choix** et à **reconnaître une limite**. Les réponses
> ci-dessous sont courtes volontairement : à l'oral, une réponse de trois phrases
> qui va au fond vaut mieux qu'un développement.
>
> Les questions marquées 🔴 sont celles qui tomberont presque à coup sûr.

---

## Architecture et choix techniques

### 🔴 « Pourquoi Flask plutôt que Django ? »

> Flask est minimal : il n'impose rien, j'assemble ce dont j'ai besoin.
> Concrètement, j'ai ajouté SQLAlchemy pour l'ORM, Flask-Login pour les sessions,
> Flask-WTF pour les formulaires et la protection CSRF. Django m'aurait donné
> tout cela d'emblée, y compris un back-office automatique — mais je ne
> maîtriserais pas ce que je n'ai pas assemblé. Sur un projet que je dois
> défendre, comprendre chaque brique comptait plus que gagner du temps. Et mes
> maquettes imposaient un back-office sur mesure, pas un back-office générique.

### 🔴 « Pourquoi pas Streamlit ? C'est plus rapide pour de la data. »

> Parce que le diplôme vise « chef de projet web » et exige une application web :
> front-office, back-office, base de données, authentification, URL publique,
> RGPD, accessibilité. Streamlit produit un outil d'analyse, pas une application
> web au sens du référentiel. Ce n'est pas une critique de Streamlit — c'est un
> choix dicté par le livrable attendu.

### « Pourquoi Jinja2 et pas React ? »

> Le rendu côté serveur suffisait : mes écrans sont des consultations, il n'y a
> pas d'interactivité complexe. Un front séparé aurait ajouté une API à
> maintenir, une seconde base de code et un déploiement supplémentaire, pour un
> gain nul ici. Chart.js couvre le besoin graphique. En solo et en temps
> contraint, c'est la solution la plus simple qui réponde au besoin.

### « Comment passez-vous de SQLite à PostgreSQL ? »

> Le code applicatif ne connaît jamais le moteur : il passe par SQLAlchemy. Le
> choix se fait dans la configuration, par la variable d'environnement
> `DATABASE_URL`. En développement elle est vide, l'application retombe sur
> SQLite ; en production, Render l'injecte depuis la base PostgreSQL. Aucune
> ligne de code applicatif ne change.

---

## Modèle de données

### 🔴 « Comment garantissez-vous que le chiffre d'affaires est juste ? »

> Une seule source de vérité : le CA est **toujours** la somme des montants des
> lignes de commande. Jamais la table `vente`, jamais `commande.montant_total`.
> C'est une règle que je me suis imposée dès la conception : deux sources qui
> calculent la même chose finissent toujours par diverger. Un test vérifie
> d'ailleurs que le CA vient bien des lignes.

### « À quoi sert la table `vente` si elle ne sert pas au CA ? »

> Elle vient du système source de Domino's, Pulse, et porte une information que
> le reste du modèle n'a pas : le **mode de paiement**. Elle alimente la
> répartition des encaissements sur l'écran d'analyse. Son montant reste cohérent
> avec la commande, mais il ne sert jamais de base de calcul.

### « Pourquoi `mot_de_passe_hash` n'est pas dans le schéma relationnel initial ? »

> Parce que ce n'est pas une donnée métier : c'est une contrainte technique de
> sécurité. Le schéma décrit le métier ; l'authentification impose de stocker une
> empreinte, jamais le mot de passe. C'est la seule addition que je me suis
> permise, et elle est documentée comme telle.

### « Pourquoi une huitième table, `import_temporaire` ? »

> Elle répond à un incident réel de production. L'import se fait en deux temps :
> analyse du fichier, puis traitement une fois la correspondance confirmée. Le
> fichier était stocké sur le disque local — ce qui marche en développement, mais
> sur un hébergement en conteneur le disque est éphémère. Un redéploiement
> effaçait le fichier en cours d'import. Il est désormais conservé en base, seul
> stockage réellement persistant, et supprimé dès le traitement terminé.

---

## Le pipeline *(le terrain le plus probable)*

### 🔴 « Que se passe-t-il si j'importe deux fois le même fichier ? »

> Rien ne bouge — et c'est voulu. Deux couches le garantissent. D'abord une
> empreinte SHA-256 du fichier : si un import réussi porte la même, l'application
> avertit et bloque par défaut. Ensuite, plus robuste, une clé déterministe par
> ligne — date, produit normalisé, quantité, montant — sous contrainte d'unicité.
> Une ligne déjà connue est ignorée, jamais réinsérée. Le récapitulatif affiche
> « 0 intégrées, N ignorées », et les indicateurs restent identiques.
>
> **Proposez-leur de le tester en direct.** C'est le geste qui emporte l'adhésion.

### « Pourquoi deux couches ? La deuxième ne suffirait pas ? »

> Si, techniquement. La clé par ligne est la couche robuste — elle couvre même le
> cas d'un fichier mêlant des lignes déjà vues et des lignes nouvelles. Mais
> l'empreinte de fichier apporte autre chose : elle **prévient l'utilisateur**
> avant le traitement, au lieu de le laisser découvrir après coup que rien n'a
> été intégré. L'une protège la donnée, l'autre informe la personne.

### 🔴 « Et si le fichier contient deux fois la même ligne, légitimement ? »

*(La question piège. Ils peuvent l'avoir trouvée en lisant le code.)*

> Vous mettez le doigt sur une limite que j'ai identifiée et documentée. Sur mon
> jeu trimestriel, un ticket contenait deux fois « Steak and Cheese XL » : un
> client a commandé deux exemplaires, enregistrés en deux lignes de quantité 1.
> Ma règle les traite comme un doublon et n'en garde qu'une. Elle protège contre
> la duplication accidentelle, mais ne sait pas la distinguer d'une répétition
> volontaire dans un même ticket. La correction consisterait à indexer la clé par
> rang d'occurrence — la première, la deuxième ligne identique. Je ne l'ai pas
> faite pour ne pas modifier une règle de qualité déjà documentée et testée si
> près du rendu.

> 💡 Reconnaître une limite, la chiffrer et savoir comment la corriger vaut mieux
> que prétendre qu'elle n'existe pas.

### « Un fichier avec des colonnes différentes, ça marche ? »

> Oui, et c'est central. J'ai séparé la source de la cible. Le schéma d'entrepôt
> est stable — date, produit, quantité, montant. La source, elle, est libre : un
> dictionnaire d'alias reconnaît les noms courants, et un écran de correspondance
> permet d'associer à la main ce qui ne l'est pas. Le séparateur et le format de
> date sont détectés automatiquement. Sans cela, la solution ne fonctionnerait
> que pour un seul logiciel de caisse.

### « Et si le fichier fait un million de lignes ? »

> Aujourd'hui, ça ne passerait pas : le traitement est synchrone, dans la requête
> web. J'ai mesuré 12 234 lignes en environ cinq secondes — après optimisation,
> car la première version mettait onze secondes. Le coût n'était pas dans les
> contrôles qualité, mais dans l'intégration : une écriture par commande et une
> requête produit par ligne. J'ai résolu les produits en une passe et supprimé
> les écritures intermédiaires. Pour un million de lignes, il faudrait passer à un
> traitement asynchrone, avec une file de tâches. La limite de 10 Mo à l'upload
> est d'ailleurs là pour cadrer l'usage.

### « Comment regroupez-vous les lignes en commandes ? »

> Par horodatage identique. Le fichier ne contient pas d'identifiant de commande :
> l'instant d'achat est le meilleur regroupement disponible. Une ligne égale un
> article, un horodatage égale un ticket. C'est un choix assumé, et c'est
> justement pour cela que la recomposition de l'heure est critique : si la date
> n'a pas d'heure, toutes les ventes d'une journée deviendraient une seule
> commande.

---

## Sécurité et accès

### 🔴 « Un équipier peut-il accéder au back-office en tapant l'URL ? »

> Non, et je peux vous le montrer. L'interface masque les liens auxquels le rôle
> n'a pas droit, mais ce n'est pas une sécurité — c'est du confort. Le contrôle
> se fait côté serveur, par un décorateur placé sur chaque route sensible : il
> vérifie le rôle avant d'exécuter la vue et renvoie une erreur 403 sinon. Des
> tests vérifient les quatre rôles sur chaque écran protégé.

### « Pourquoi des décorateurs plutôt qu'une librairie de permissions ? »

> La logique tient en quinze lignes et je peux l'expliquer entièrement. Une
> librairie m'aurait apporté de la souplesse dont je n'ai pas besoin — je n'ai
> que quatre rôles et une matrice fixe — au prix d'une dépendance que je
> maîtriserais moins.

### « Comment vous protégez-vous des injections SQL ? »

> Je n'écris pas de SQL : je passe par l'ORM, qui paramètre les requêtes. Les
> valeurs saisies ne sont jamais concaténées dans une requête. C'est un bénéfice
> collatéral de SQLAlchemy, mais c'en est un réel.

### « Et le CSRF ? »

> Tous les formulaires passent par Flask-WTF, qui insère un jeton dans chaque
> formulaire et le vérifie côté serveur. Une requête POST sans jeton valide est
> refusée. Je l'ai constaté pendant les tests : mes premiers appels automatisés
> étaient rejetés — c'était la preuve que la protection fonctionnait.

### « Où sont stockés les mots de passe ? »

> Seule une empreinte est stockée, produite par Werkzeug avec un sel. La
> vérification compare des empreintes, jamais des mots de passe. Un test vérifie
> qu'aucun mot de passe n'apparaît en clair en base.

---

## Tests et fiabilité

### « Qu'est-ce qui n'est pas testé ? »

> L'interface elle-même n'a pas de tests automatisés : pas de tests de rendu, pas
> de tests de bout en bout dans un navigateur. Je les ai faits manuellement, sur
> plusieurs résolutions. Mes tests couvrent la logique — indicateurs, pipeline,
> rôles, idempotence, opportunités — parce que c'est là qu'une erreur serait
> invisible et coûteuse. Une erreur d'affichage se voit ; un chiffre d'affaires
> faux, non.

### « Comment testez-vous une recommandation ? »

> C'est justement l'avantage d'une règle explicite. J'injecte des données dont je
> connais le résultat attendu : trois créneaux chargés, un créneau faible, et je
> vérifie que seul celui-là ressort. Je teste aussi le cas inverse — un créneau à
> trop faible volume ne doit rien déclencher. Avec un modèle appris, je ne
> pourrais pas écrire ce test.

---

## La couche décisionnelle

### 🔴 « Pourquoi pas de machine learning pour la prévision ? »

> Parce que la méthode simple répond au besoin et que je peux l'expliquer en une
> phrase : l'affluence d'un créneau est la moyenne des créneaux équivalents
> passés, même jour de la semaine, même heure. C'est robuste, transparent, et
> suffisant pour du staffing. Un modèle appris demanderait plus de données, un
> entraînement, une validation — et surtout, un responsable de magasin
> n'appliquera pas une recommandation qu'il ne comprend pas. Je l'ai noté comme
> évolution, pas comme manque.

### « Vos recommandations de promotion, elles valent quoi ? »

> Ce sont des signaux, pas des décisions — et je l'affiche à l'écran. Elles
> pointent des écarts sans les expliquer : un créneau creux peut relever d'une
> fermeture ou d'un effectif réduit. La plus solide est l'analyse des
> associations, parce qu'elle repose sur un comportement déjà observé : les
> clients qui prennent Pepperoni et Reine ensemble ont un panier supérieur de
> presque vingt euros. Créer cette formule ne relève pas d'une prédiction.
>
> Ma limite la plus nette : sans historique de promotions, je ne peux pas mesurer
> l'effet d'une opération passée. C'est l'évolution la plus utile.

---

## Déploiement

### « Comment déployez-vous ? »

> L'infrastructure est décrite dans `render.yaml` : une base PostgreSQL et un
> service web. Au démarrage, la séquence applique les migrations, amorce les
> données si la base est vide, puis lance Gunicorn. Un push sur la branche
> déclenche le redéploiement. La clé secrète est générée par la plateforme,
> jamais dans le dépôt.

### « Quelles sont les limites de votre hébergement ? »

> L'offre gratuite met l'instance en veille après quinze minutes d'inactivité :
> le premier chargement prend trente à soixante secondes. Le disque est
> éphémère — ce qui m'a d'ailleurs coûté un incident, corrigé depuis. Pour un
> usage réel, il faudrait une offre payante.

### « Que se passe-t-il si une migration échoue en production ? »

> J'ai rencontré le cas. Une base dont le registre de migrations est désynchronisé
> échouait sur « table déjà existante », et bloquait toutes les migrations
> suivantes. J'ai rendu les migrations défensives : chaque table ou colonne n'est
> créée que si elle est absente. Une base en retard peut ainsi rattraper sans
> échouer. J'ai vérifié sur quatre scénarios, dont l'aller-retour complet.

---

## Cas pratiques *(ils peuvent vous demander de raisonner à voix haute)*

### « Comment ajouteriez-vous la gestion de plusieurs magasins ? »

> Le modèle le permet déjà : `point_de_vente` existe, et commandes comme
> utilisateurs y sont rattachés. Le travail porterait sur trois points : un
> sélecteur de point de vente dans l'interface, l'adaptation des services KPI qui
> reçoivent aujourd'hui un identifiant unique, et surtout une règle d'accès —
> qui peut voir quel magasin. C'est cette dernière question, métier, qui serait
> la plus structurante.

### « Comment ajouteriez-vous un champ à l'import ? »

> Comme j'ai ajouté le mode de paiement. Trois étapes : la colonne sur le modèle
> avec une migration, une entrée dans le dictionnaire d'alias en champ facultatif,
> et sa prise en compte à l'intégration. Le champ apparaît alors automatiquement
> dans l'écran de correspondance. Son absence dans un fichier ne provoque aucune
> erreur.

### « Un utilisateur signale un chiffre d'affaires faux. Comment procédez-vous ? »

> Je remonte la chaîne. D'abord le journal des imports : quel fichier, quand,
> combien de lignes lues, intégrées, rejetées, ignorées. Si des lignes ont été
> rejetées, le récapitulatif dit pourquoi. Ensuite je vérifie que le CA vient
> bien des lignes de commande — c'est la source unique. C'est précisément pour ce
> genre de situation que j'ai construit la traçabilité : reconstituer ce qui
> s'est passé plutôt que d'avancer par hypothèses.

---

## Les trois réflexes

1. **Si tu ne sais pas** — « Je ne l'ai pas traité. Voici comment je m'y
   prendrais. » Un jury pardonne une lacune, jamais un bluff.
2. **Ramène toujours au concret** — un chiffre, un fichier, un écran. Tu peux
   tout montrer en direct.
3. **Assume tes limites avant qu'on te les oppose.** Elles sont documentées dans
   ton rapport et affichées dans ton application : c'est une force, pas un aveu.
