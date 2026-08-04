# Prompt — Audit de conformité du rapport de PFE

> **Mode d'emploi.** Ouvre une **discussion neuve** (ne réutilise pas celle qui a
> servi à rédiger : un correcteur qui a écrit le texte ne voit plus ses trous).
> Copie-colle tout ce document, et joins :
>
> 1. `PFE_rapport_VALIDE_2.docx` — la version la plus récente de ton rapport ;
> 2. **le guide / référentiel de l'école** (PDF, consignes, grille d'évaluation) ;
> 3. les 6 captures de `docs/captures/` — facultatif mais recommandé.
>
> Si tu n'as pas le guide sous la main, dis-le : le prompt prévoit un repli sur
> le référentiel RNCP40857. Mais **ce repli est moins bon** — récupère le guide.

---

## Ton rôle

Tu es **examinateur**, pas relecteur. Ton travail n'est pas d'améliorer mon
rapport : c'est de trouver ce qui le ferait perdre des points, avant que le jury
ne le trouve.

Trois règles de posture :

1. **Ne me félicite pas.** Ce qui est bon, tu le mentionnes en une ligne et tu
   passes. Ton temps utile est sur ce qui manque.
2. **Cite avant de juger.** Chaque remarque s'appuie sur une citation exacte du
   rapport (ou sur le constat qu'un passage est *absent*). Pas d'impression
   générale.
3. **Ne réécris rien** dans cette passe. Tu produis un diagnostic. La correction
   viendra ensuite, une fois que j'aurai arbitré.

Si un point est ambigu et que la réponse change ton verdict, pose-moi la
question au lieu de supposer.

---

## Le contexte

Projet de fin d'études — Bachelor Data & Business Intelligence, Nexa Digital
School. Titre visé : **Chef de projet web (RNCP40857)**.

Le livrable est une application web réellement déployée : **une plateforme
décisionnelle de pilotage d'un point de vente Domino's Pizza** (cas
d'application : magasin de **Chatou, 78**). Le rapport documente cette
application. Le jury la manipulera pendant la soutenance.

**C'est le point qui commande tout l'audit :** le jury aura le rapport dans une
main et l'application dans l'autre. Le moindre écart entre les deux — un nombre
d'écrans, un nom de ville, un chiffre — est un écart qu'il verra.

---

# Mission 1 — Conformité au guide de l'école

**Si je t'ai joint le guide :** c'est lui qui fait autorité, pas tes habitudes.
Procède ainsi :

1. **Extrais du guide la liste exhaustive des attendus** : parties obligatoires,
   ordre imposé, volume attendu, annexes exigées, format (pagination, sommaire,
   bibliographie, page de garde, résumé, mots-clés), critères de la grille
   d'évaluation s'il y en a une.
2. **Restitue-la sous forme de tableau**, une ligne par attendu, avec une colonne
   « présent dans mon rapport ? » — ✅ / ⚠️ partiel / ❌ absent — et, pour chaque
   ✅ ou ⚠️, **le numéro de section où tu l'as trouvé**.
3. **N'invente aucun attendu** qui ne serait pas dans le guide. Si le guide est
   muet sur un point, écris « non exigé par le guide » plutôt que d'appliquer une
   convention générale.

**Si je ne t'ai pas joint le guide :** dis-le explicitement en tête de ta réponse
(« audit réalisé sans le guide de l'école — fiabilité réduite »), puis fais le
même exercice contre les blocs de compétences du titre **RNCP40857 — Chef de
projet web**, en particulier :

- l'analyse du besoin et le cadrage (cahier des charges, expression du besoin) ;
- la conception (architecture, modèle de données, maquettes, arborescence) ;
- le pilotage de projet (planification, méthode, arbitrages, gestion des risques) ;
- la réalisation et les tests ;
- le déploiement, la sécurité, la conformité RGPD, l'accessibilité ;
- le recul critique (limites, perspectives, bilan personnel).

---

# Mission 2 — Structure et organisation

Réponds à ces questions, chacune adossée à une citation :

| # | Question |
|---|---|
| 1 | La progression est-elle **logique** : besoin → cahier des charges → conception → réalisation → tests → déploiement → recul ? Y a-t-il un chapitre à sa mauvaise place ? |
| 2 | Y a-t-il des **redites** — le même argument développé dans deux sections ? Indique laquelle des deux garder. |
| 3 | Le **déséquilibre de volume** : quelle partie est manifestement trop courte au regard de son poids dans l'évaluation ? |
| 4 | Les **transitions** entre parties existent-elles, ou les chapitres sont-ils juxtaposés ? |
| 5 | Chaque **choix technique** est-il justifié par un besoin métier énoncé plus haut, ou certains tombent-ils du ciel ? |
| 6 | Les **annexes** sont-elles appelées dans le corps du texte ? Une annexe jamais citée est une annexe morte. |
| 7 | L'**introduction annonce-t-elle le plan réellement suivi** ? La conclusion répond-elle à la problématique posée en introduction ? |
| 8 | Les **figures et captures** sont-elles numérotées, légendées, et **commentées dans le texte** ? Une capture posée sans commentaire ne prouve rien. |

Signale aussi, sans t'y étendre : incohérences de temps verbaux (je/nous, passé/présent),
titres de sections qui ne décrivent pas leur contenu, sommaire désynchronisé.

---

# Mission 3 — Exactitude par rapport à l'application livrée *(la plus importante)*

Ci-dessous, **la fiche de vérité** de l'application au 4 août 2026. Elle a été
établie depuis le code source, pas de mémoire.

**Ta tâche : passer chaque élément de cette fiche au crible du rapport.** Pour
chacun, réponds : *exact / contredit par le rapport / absent du rapport*. Quand
c'est contredit, **cite la phrase fautive et donne la correction**.

## Fiche de vérité — architecture

- Stack : **Python / Flask** (application factory + blueprints), **SQLAlchemy**,
  **Flask-Migrate** (Alembic), **Flask-Login**, **Flask-WTF** (CSRF), **pandas**.
- Front : **gabarits Jinja2** rendus côté serveur + **Chart.js** (servi en local,
  pas depuis un CDN). **Aucun framework front séparé.**
- Base : **SQLite en développement**, **PostgreSQL en production**, bascule
  automatique par la variable `DATABASE_URL`, **sans modification du code**.
- Serveur de production : **gunicorn**. Hébergement : **Render**, décrit en
  *infrastructure as code* dans `render.yaml`.
- 6 blueprints : `auth`, `dashboard`, `ventes`, `admin`, `imports`, `legal`.
- 5 services métier : `kpi`, `pipeline`, `alertes`, `prevision`, `opportunites`.

## Fiche de vérité — modèle de données : **8 tables**

`point_de_vente` · `utilisateur` · `produit` · `commande` · `ligne_commande` ·
`vente` · `import_fichier` · `import_temporaire`

Trois points à vérifier **mot pour mot** dans le rapport :

1. Le **chiffre d'affaires est calculé exclusivement depuis `ligne_commande`**.
   La table `vente` (issue de l'export Pulse, avec le mode de paiement) ne
   participe **jamais** au calcul du CA. C'est l'invariant central du modèle : si
   le rapport laisse entendre l'inverse, c'est une faute lourde.
2. `import_temporaire` est une **table technique**, ajoutée pour stocker les
   fichiers pendant l'import — le disque de l'hébergeur est éphémère. Si le
   rapport annonce « sept tables », c'est qu'il date d'avant cet ajout.
   Formulation acceptable : *« sept tables métier, plus une table technique »*.
3. `ligne_commande` porte une **clé d'idempotence** (empreinte SHA-256
   déterministe) sous contrainte d'unicité.

## Fiche de vérité — les **6 écrans**

| # | Écran | Accessible à |
|---|---|---|
| 1 | Tableau de bord (indicateurs, alertes, graphiques) | tous les rôles |
| 2 | Analyse des ventes (+ prévision, modes de paiement, export) | manager, assistant, premier équipier |
| 3 | Produits | manager, assistant, premier équipier |
| 4 | **Opportunités promotionnelles** | manager, assistant, premier équipier |
| 5 | Administration — utilisateurs & sources | manager, assistant |
| 6 | Import de données (pipeline) | manager, assistant |

⚠️ L'écran **Opportunités** est le plus récent. **Vérifie qu'il figure partout** :
arborescence, cahier des charges, matrice des rôles, description fonctionnelle,
captures, conclusion. C'est l'oubli le plus probable du rapport.

⚠️ Traque toute occurrence de « **cinq écrans** » : le décompte est **six**.

## Fiche de vérité — les 4 rôles

`manager` · `assistant manager` · `premier équipier` · `équipier`

Gestion **volontairement manuelle** : un champ `role` sur `utilisateur` + des
décorateurs de contrôle d'accès, sans bibliothèque tierce. Le contrôle est
**côté serveur** : masquer un bouton dans l'interface n'est pas une sécurité.

## Fiche de vérité — le pipeline d'import

Cinq étapes : **lecture → correspondance des colonnes → contrôles qualité →
résolution des produits → intégration**.

- Détection automatique du séparateur ; plusieurs formats de date acceptés.
- **Découplage source / cible** : les colonnes du fichier source sont libres, le
  schéma cible est stable ; un dictionnaire d'alias les rapproche, et un écran de
  correspondance manuelle traite le reste. C'est ce qui rend la solution
  déployable sur un parc de magasins sans redéveloppement.
- Champs obligatoires : `date`, `produit`, `quantite`, `montant`.
  Champs optionnels : `heure`, `mode_paiement`.
- Contrôles rejetant une ligne : valeur manquante, doublon interne, format de
  date invalide, quantité invalide, montant invalide. **Le rejet est toujours
  motivé et affiché** — jamais silencieux.
- **Idempotence** : empreinte SHA-256 du fichier (détection de réimport, blocage
  par défaut, forçage possible) **et** clé déterministe par ligne. Réimporter le
  même fichier donne **0 ligne intégrée, N ignorées, indicateurs inchangés**.

## Fiche de vérité — la couche décision

Trois briques, **toutes à base de règles déterministes explicites — aucun
apprentissage automatique, aucun modèle statistique entraîné** :

1. **Alertes** — écarts significatifs par rapport à l'habitude (seuils explicites).
2. **Prévision d'affluence** — extrapolation par moyennes historiques.
3. **Opportunités promotionnelles** — trois questions : *quand agir* (créneaux
   creux), *quoi pousser* (produits en retrait), *quelles formules créer*
   (associations de produits).

Si le rapport parle de « machine learning », « IA », « prédictif » ou
« algorithme d'apprentissage » à propos de ces briques, **c'est à corriger** :
c'est exactement la promesse qu'un jury technique testera, et le code ne la tient
pas — délibérément.

## Fiche de vérité — les chiffres vérifiables

Le jury peut rejouer ces chiffres à l'écran. Vérifie **chaque occurrence** :

| Élément | Valeur exacte |
|---|---|
| Fichier conforme (`ventes_demo_juillet.csv`) | **186 lues / 186 intégrées / 0 rejetée** |
| Fichier avec anomalies (`ventes_sale.csv`) | **25 lues / 14 intégrées / 11 rejetées** |
| Détail des 11 anomalies | **3 manquantes · 1 doublon · 3 dates · 2 quantités · 2 montants** |
| Fichier aux colonnes exotiques | **20 lues / 20 intégrées / 0 rejetée** |
| Jeu de volume (`ventes_dominos_T1_2026.csv`) | **12 234 lignes · 5 370 commandes · 32 produits** |
| Optimisation du traitement | **≈ 11 s → ≈ 5 s** |
| Créneau le plus creux | **16 h – 17 h, −71 %** |
| Association la plus rentable | **Pepperoni + Reine, panier +19,74 €** |
| Tests automatisés | **66 tests (pytest)**, 10 fichiers de test |
| Captures d'exécution fournies | **6** |

## Fiche de vérité — sécurité, conformité, limites

- Mots de passe **hachés**, jamais stockés en clair.
- **CSRF** sur les formulaires, sessions sécurisées, **HTTPS** en production.
- RGPD : bandeau cookies, mentions légales, CGU, politique de confidentialité,
  suppression de compte.
- **Aucune donnée réelle de l'entreprise n'est diffusée** : l'application
  fonctionne sur un **jeu de données représentatif**. Ce point doit être écrit
  noir sur blanc dans le rapport — c'est une exigence de confidentialité, pas un
  détail.
- **Point de vente : Chatou (78).** ⚠️ Une version antérieure du rapport
  mentionnait **Nanterre**. **Cherche toute occurrence résiduelle de
  « Nanterre »** — dans le corps, les captures, les annexes, les adresses e-mail
  (`@pdv-chatou.fr`), les légendes. C'est le type d'oubli qui se voit.
- Limites assumées à vérifier dans la conclusion : hébergement gratuit mettant
  l'instance en veille ; absence d'historique de promotions empêchant de mesurer
  l'effet d'une opération passée ; les pistes décisionnelles **signalent** des
  écarts sans les **expliquer**.

---

# Ce que je veux en retour

Dans cet ordre exact, et rien d'autre :

### 1. Verdict en trois lignes

Le rapport est-il **livrable en l'état** ? Oui / Non / Oui sous réserve. Et si
non : le seul point qui bloque.

### 2. Les écarts bloquants

Ce qui coûterait des points ou serait contredit par l'écran. Format :

> **[BLOQUANT] § 8.2 — « sept tables »**
> Le modèle en compte huit depuis l'ajout de `import_temporaire`.
> → Remplacer par « sept tables métier, plus une table technique de dépôt ».

### 3. Les écarts secondaires

Même format, préfixe `[SECONDAIRE]`.

### 4. Le tableau de conformité au guide

Celui de la mission 1.

### 5. Les manques

Ce qui est attendu et **totalement absent** — pas une phrase à corriger, une
section à écrire. Pour chacun : où l'insérer, et en combien de mots.

### 6. Le plan d'action

Une liste ordonnée par **rapport gain / temps**, avec une estimation en minutes
pour chaque ligne. Je veux savoir par quoi commencer si je n'ai que deux heures.

---

## Ce que tu ne dois pas faire

- ❌ Réécrire des paragraphes entiers dans cette passe — je veux le diagnostic
  d'abord, l'arbitrage m'appartient.
- ❌ Proposer d'ajouter des fonctionnalités à l'application. **Le code est gelé.**
  Le rapport décrit ce qui existe ; il ne promet rien de plus.
- ❌ Signaler du style ou de la formulation tant qu'il reste un écart factuel non
  traité. La hiérarchie est : *faux* > *manquant* > *mal placé* > *mal écrit*.
- ❌ Supposer. Si tu ne peux pas trancher sans une information que je n'ai pas
  fournie, pose-moi la question — elle sera plus utile qu'une remarque prudente.
