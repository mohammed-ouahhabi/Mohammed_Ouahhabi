# Script de démonstration — soutenance

> Objectif : une démonstration de **8 à 10 minutes**, insérée dans la présentation
> après la diapositive 11. Les diapositives 09 à 11 restent le filet de sécurité :
> si l'application ne répond pas, tu déroules les chiffres sans t'interrompre.

---

## Avant d'entrer dans la salle

### La veille

| # | Action | Pourquoi |
|---|---|---|
| 1 | `git pull` puis vérifier que Render est sur le dernier commit | l'application en ligne doit correspondre au rapport |
| 2 | Se connecter en Manager → **Réinitialiser les données de démonstration** | données propres, indicateurs justes, point de vente « Chatou » |
| 3 | Relever la **valeur de l'alerte affichée** et la reporter si ta diapositive 11 la cite | les données changent à chaque réinitialisation |
| 4 | Télécharger les 4 fichiers de `sample_data/` sur le bureau | ne pas fouiller dans l'arborescence devant le jury |

### 5 minutes avant

| # | Action |
|---|---|
| 1 | **Ouvrir l'URL pour réveiller l'instance** — 30 à 60 s sur l'offre gratuite |
| 2 | Se connecter en `manager@pdv-chatou.fr` / `motdepasse123` |
| 3 | Ouvrir **deux onglets** : l'un sur le tableau de bord, l'autre sur l'import |
| 4 | Fermer messageries, notifications, autres fenêtres |
| 5 | Garder le PDF de la présentation ouvert en secours |

> **Règle absolue** : ne jamais réinitialiser les données pendant la
> démonstration. Tu serais déconnecté et le seed prend quelques secondes.

---

## Le déroulé, minute par minute

### 1. Le tableau de bord — 2 min

**Tu montres :** l'écran d'accueil après connexion.

> « Voici ce que voit le responsable en arrivant le matin. Quatre indicateurs, et
> surtout, tout en haut, un bandeau *À surveiller*. »

**Tu insistes sur l'ordre :** l'alerte est **avant** les indicateurs.

> « Ce n'est pas un choix esthétique. Un responsable n'a pas le temps de lire un
> tableau de bord entier : ce qui exige une décision doit apparaître en premier. »

**Tu fais défiler** : évolution du CA, top produits, pics d'activité.

> « Ces graphiques ne sont pas des illustrations : ils sont calculés à la volée
> depuis la base, à chaque affichage. »

### 2. Le pipeline — 4 min *(le cœur de la démonstration)*

Bascule sur l'onglet **Import de données**.

**a) Le fichier propre** — `ventes_demo_juillet.csv`

> « Je charge un export de ventes. Première étape : l'application lit les
> en-têtes et me propose une correspondance. »

Montre l'écran de correspondance, les badges verts « détecté ».

> « Les colonnes ont été reconnues automatiquement. »

Lance l'import.

> « 186 lignes lues, 186 intégrées, aucune rejetée. »

**b) Le fichier sale** — `ventes_sale.csv`

> « Maintenant un fichier tel qu'on en reçoit vraiment. »

> « 25 lues, 14 intégrées, **11 rejetées**. Et surtout : le détail des anomalies.
> Trois valeurs manquantes, un doublon, trois dates au mauvais format, deux
> quantités et deux montants invalides. Le rejet est mesuré, jamais silencieux —
> le responsable sait exactement ce qui n'est pas passé et pourquoi. »

**c) Les colonnes exotiques** — `ventes_colonnes_exotiques.csv`

> « Un autre magasin, un autre logiciel de caisse. Séparateur point-virgule,
> colonnes nommées différemment. »

Montre : `horodatage` et `nb` détectés, `libelle_article` et `total_ttc` à
associer. Tu les associes à la main.

> « La source est libre, la cible est stable. C'est une couche de correspondance
> qui les relie — c'est ce qui rend la solution déployable sur tout un parc, sans
> redéveloppement. »

**d) L'idempotence** — *le moment fort*

Recharge **le même fichier** que celui du point (a).

> « Que se passe-t-il si je réimporte un fichier déjà traité ? »

L'écran d'avertissement apparaît.

> « L'application a calculé l'empreinte du fichier, l'a reconnue, et bloque par
> défaut. Mais allons plus loin : je force. »

Clique « Continuer quand même ».

> « **Zéro ligne intégrée, N ignorées.** Chaque ligne porte une clé déterministe :
> celles déjà présentes ne sont jamais réinsérées. »

Retourne au tableau de bord.

> « Et le chiffre d'affaires est inchangé. C'est la différence entre un pipeline
> de démonstration et un pipeline fiable. »

> 💡 **C'est le moment que le jury retiendra.** Ne le précipite pas.

### 3. Les opportunités — 2 min

Ouvre l'écran **Opportunités**.

> « Le tableau de bord dit ce qui s'est passé, les alertes ce qui mérite
> attention. Cet écran propose des actions. Trois questions, dans l'ordre :
> quand agir, quoi pousser, quelles formules créer. »

Montre le graphique des créneaux, barres rouges sous la moyenne.

> « Le créneau 16h-17h fait 71 % de moins qu'une heure moyenne. »

Descends jusqu'aux associations.

> « Et voici le chiffre que je retiens : les clients qui prennent Pepperoni et
> Reine ensemble ont un panier moyen supérieur de **presque vingt euros**. Ce
> n'est pas une prédiction, c'est un comportement déjà observé. Créer cette
> formule est une décision immédiate, appuyée sur une donnée mesurée. »

**Puis, avant qu'on te le demande**, montre le bloc « Limites » :

> « J'affiche les limites à l'écran : ces pistes signalent des écarts, elles ne
> les expliquent pas. Un créneau creux peut relever d'une fermeture. Et sans
> historique de promotions, je ne peux pas mesurer l'effet d'une opération déjà
> menée. »

### 4. Les rôles — 1 min *(à ne pas oublier)*

Déconnecte-toi, reconnecte-toi en `equipier@pdv-chatou.fr`.

> « Même application, autre rôle. La barre latérale a changé : plus
> d'administration, plus d'import, plus d'analyse. »

**Puis tape directement l'URL** `/administration/` dans la barre d'adresse.

> « Et si je tente d'y accéder par l'URL… accès refusé. L'interface masque, mais
> c'est le serveur qui contrôle. C'est une distinction essentielle : cacher un
> bouton n'est pas une sécurité. »

> 💡 **Fais-le sans qu'on te le demande.** C'est exactement le test qu'un jury
> technique voudrait faire lui-même.

---

## Si quelque chose échoue

| Problème | Réaction |
|---|---|
| L'instance ne répond pas | *« L'hébergement gratuit met l'instance en veille — c'est une limite que j'assume et que j'ai documentée. »* Enchaîne sur les diapositives 09-11, reviens plus tard. |
| Un import échoue | *« Voyons le message. »* Lis-le à voix haute : les messages sont explicites, c'est un atout. Puis passe au fichier suivant. |
| Une page renvoie une erreur | Ne masque pas. *« Regardons ce qu'elle dit. »* Les pages d'erreur nomment la cause. |
| Le temps manque | Coupe le point 3 (opportunités), **jamais** le point 2d (idempotence) ni le point 4 (rôles). |

> Ne dis jamais « normalement ça marche ». Dis ce que tu observes, et ce que tu
> en déduis. Un incident bien analysé impressionne davantage qu'une démonstration
> lisse.

---

## L'ordre de priorité, si tu dois couper

1. **Idempotence** (2d) — le différenciant technique
2. **Rôles par URL** (4) — la preuve de sécurité
3. **Fichier sale** (2b) — la qualité des données
4. Tableau de bord (1)
5. Colonnes exotiques (2c)
6. Opportunités (3)
