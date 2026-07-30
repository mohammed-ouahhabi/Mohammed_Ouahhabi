# Mise à jour du rapport — écarts entre le document et l'application

> Établi en confrontant `PFE_rapport_VALIDE_2.docx` au code réellement déployé.
> Le rapport est complet et bien écrit ; il évite les chiffres figés, ce qui le
> protège du vieillissement. Restent **cinq ajouts** (fonctionnalités
> développées après sa rédaction) et **une correction** dans le cahier des
> charges. L'incohérence de nom du point de vente est, elle, déjà résolue côté
> application (§ 4).

---

## 1. AJOUT — L'idempotence des imports (le plus important)

**Absent du rapport** : aucune occurrence d'« idempotence », « empreinte de
fichier », « réimport » ou « lignes ignorées ». C'est pourtant le correctif le
plus différenciant du projet, et un jury technique teste exactement cela.

### 1.1. Où l'insérer — § 10.7 « La gouvernance : contrôles qualité et traçabilité »

La section liste aujourd'hui : *« Doublons — deux lignes strictement identiques
sont dédupliquées. »* Cette formulation est désormais **incomplète** : elle ne
décrit que le dédoublonnage *à l'intérieur* d'un fichier.

**Texte à ajouter après la liste des contrôles :**

> **L'idempotence : un import rejouable sans fausser les indicateurs.**
> Un contrôle qualité ligne à ligne ne suffit pas : il dédoublonne *au sein* d'un
> fichier, mais rien n'empêche de réimporter deux fois le même export — et de
> doubler mécaniquement le chiffre d'affaires. Le pipeline garantit donc
> l'idempotence **entre imports**, par deux couches complémentaires.
>
> La première agit au niveau du fichier : une empreinte SHA-256 de son contenu
> est calculée et journalisée. Si un import réussi porte déjà la même empreinte,
> l'interface avertit l'utilisateur et bloque la réintégration par défaut, une
> option explicite permettant de poursuivre en connaissance de cause.
>
> La seconde, plus robuste, agit au niveau de la ligne : chaque ligne reçoit une
> clé déterministe dérivée de ses données métier — date, produit normalisé,
> quantité, montant — soumise à une contrainte d'unicité en base. À
> l'intégration, une ligne dont la clé existe déjà est ignorée, jamais
> réinsérée. Cette couche couvre aussi le recouvrement partiel, c'est-à-dire un
> fichier mêlant des lignes déjà connues et des lignes nouvelles.
>
> Conformément au principe de rejet mesuré et non silencieux, ces lignes ignorées
> ne disparaissent pas : elles sont comptées séparément des lignes rejetées,
> affichées dans le récapitulatif d'import et conservées dans le journal.
> Réimporter un fichier connu affiche explicitement *« lignes lues : N,
> intégrées : 0, ignorées : N »*, et les indicateurs restent inchangés.

### 1.2. Où l'insérer aussi — § 16.3 « La gestion des correctifs »

La section décrit la *méthode* de correction sans l'illustrer. **Ajouter un
exemple concret :**

> À titre d'illustration, un défaut de fiabilité a été identifié en exploitation :
> réimporter un fichier déjà traité réinsérait les ventes et gonflait le chiffre
> d'affaires. Le correctif — la double couche d'idempotence décrite au § 10.7 — a
> été développé localement, couvert par sept tests dédiés (réimport à
> l'identique, recouvrement partiel, journalisation), validé par la suite de
> tests complète, puis déployé. Une action d'administration réservée au manager
> permet par ailleurs de repartir d'un jeu de données propre.

### 1.3. Nuance à ajouter — la limite assumée de la règle « doublons »

Point d'honnêteté qui **impressionnera** un jury, à placer en fin de § 10.7 :

> La règle de dédoublonnage a une limite assumée. Sur le jeu trimestriel, un
> ticket comportait deux lignes strictement identiques (deux fois le même article
> au même instant) : le contrôle les traite comme un doublon et n'en retient
> qu'une, alors qu'il s'agit d'un achat légitime de deux exemplaires. La règle
> protège contre la duplication accidentelle mais ne sait pas la distinguer d'une
> répétition volontaire au sein d'un même ticket. L'évolution consisterait à
> indexer la clé d'idempotence par rang d'occurrence.

---

## 2. AJOUT — La recomposition de l'horodatage

**Absent du rapport.** À insérer en § 10.6 « Le connecteur : une couche de
correspondance ».

> **Recomposition de l'horodatage.** Certains exports de caisse séparent la date
> et l'heure en deux colonnes distinctes. Le connecteur accepte donc une colonne
> « heure » facultative et recompose l'horodatage complet avant l'analyse.
> L'enjeu n'est pas cosmétique : les lignes étant regroupées en commandes par
> horodatage, une date sans heure agrégerait toutes les ventes d'une journée en
> une seule commande — faussant le nombre de commandes, le panier moyen et les
> pics horaires. Deux garde-fous encadrent la règle : si la colonne date porte
> déjà une heure, elle fait foi ; si l'heure est absente ou illisible sur une
> ligne, la date seule est conservée, car l'heure est une précision et non une
> condition de validité.

---

## 3. AJOUT — Volume réel et performance

**§ 13.9 « Les mesures de performance »** ne mentionne aucun test de charge.
C'est une faiblesse : le jury peut demander « et sur un vrai volume ? ».

> **Tenue en charge.** Le pipeline a été éprouvé sur un export trimestriel réel
> de 12 234 lignes (janvier à mars 2026), produisant 5 370 commandes et
> 32 produits distincts. Le traitement complet — lecture, contrôles qualité,
> intégration — s'exécute en environ cinq secondes.
>
> Cette mesure a d'ailleurs conduit à une optimisation. Une première version
> traitait le même fichier en onze secondes. L'analyse a montré que le coût ne
> venait pas du parcours ligne à ligne des contrôles qualité — moins d'une
> seconde — mais de l'intégration : une écriture intermédiaire par commande, soit
> plus de cinq mille, et une requête produit par ligne. Les produits sont
> désormais résolus en une seule passe et les objets créés via les relations de
> l'ORM, sans écriture intermédiaire. Le temps a été divisé par deux, à logique
> de contrôle qualité strictement inchangée.

**Annexe 3 — Jeux de données de test** : ajouter un quatrième jeu.

> **Jeu 4 — Fichier de volume réel.** Export trimestriel de 12 234 lignes.
> Objectif : vérifier la tenue en charge et la justesse des indicateurs sur un
> volume représentatif d'une exploitation réelle.

---

## 3 bis. AJOUT — Le stockage du fichier entre les deux étapes de l'import

Défaut identifié **en production**, à ajouter en § 15.6 « Les limites et l'accès »
ou en § 16.3 comme second exemple de correctif.

> **Une contrainte propre à l'hébergement en conteneur.** L'import se déroule en
> deux temps : le fichier est d'abord analysé pour proposer une correspondance de
> colonnes, puis traité une fois celle-ci confirmée. Il doit donc être conservé
> entre deux requêtes. La première version l'écrivait sur le disque local — ce
> qui fonctionne en développement, mais s'est révélé fragile en production : sur
> un hébergement de type conteneur, le système de fichiers est éphémère. Un
> redéploiement ou une mise en veille de l'instance efface le fichier, et
> l'utilisateur se voit répondre que son dépôt est introuvable au moment de
> valider.
>
> Le fichier est désormais conservé **en base de données** le temps du
> traitement, la base étant le seul stockage réellement persistant de
> l'application. Le dépôt est supprimé dès le traitement terminé, et purgé au
> bout d'une heure en cas d'abandon. Cet incident illustre une différence
> structurante entre un environnement de développement et un environnement de
> production : ce qui est acquis localement — la persistance du disque — ne l'est
> pas nécessairement une fois déployé.

---

## 3 ter. AJOUT — L'écran « Opportunités promotionnelles »

Nouvelle brique développée après la rédaction : à décrire en Partie 2, aux côtés
des alertes et de la prévision.

> **Des écarts aux actions.** Une troisième brique décisionnelle propose des
> actions commerciales chiffrées, organisées selon trois questions : quand agir
> (créneaux dont le chiffre d'affaires est nettement sous la moyenne horaire),
> quoi pousser (produits dont la part de chiffre d'affaires est en retrait), et
> quelles formules créer (paires de produits les plus souvent achetées ensemble).
> Chaque proposition est accompagnée des chiffres qui la fondent — manque à
> gagner estimé, part de chiffre d'affaires, panier moyen des commandes
> concernées comparé au panier global.
>
> Comme la prévision, cette brique repose sur des règles explicites et non sur un
> apprentissage automatique. Une recommandation qu'un responsable ne peut pas
> comprendre est une recommandation qu'il n'appliquera pas ; c'est aussi ce qui
> rend chaque règle testable, avec des résultats connus d'avance. Les limites
> sont affichées à l'écran : ces pistes signalent des écarts sans les expliquer,
> et l'application ne conservant aucun historique de promotions, elle ne peut pas
> mesurer l'effet d'une opération déjà menée.

---

## 3 quater. À CORRIGER — Le cahier des charges annonce cinq écrans

Le cahier des charges est une **section du rapport** (§ 9), il se met donc à jour
avec lui. Son § 9.2 « Les fonctionnalités détaillées » ouvre sur :

> « La solution s'organise autour de **cinq écrans**… »

L'application en compte désormais **six**. Deux corrections :

1. Remplacer « cinq écrans » par « six écrans ».
2. Ajouter la description du nouvel écran, après l'écran 5 :

> **Écran 6 — Opportunités promotionnelles (front-office).** Prolongement de
> l'analyse : l'écran ne se contente pas de restituer les ventes, il propose des
> actions commerciales chiffrées, organisées selon trois questions — quand agir
> (créneaux horaires dont le chiffre d'affaires décroche), quoi pousser (produits
> dont la part de chiffre d'affaires est en retrait) et quelles formules créer
> (produits fréquemment achetés ensemble). Chaque proposition s'accompagne des
> chiffres qui la fondent. L'accès est aligné sur celui de l'analyse des ventes.

> **Cohérence à vérifier** : les sections qui énumèrent les écrans doivent suivre
> — notamment § 11.3 « Les cinq écrans maquettés » (les maquettes d'origine en
> comptaient bien cinq : préciser que le sixième écran est né d'une évolution
> postérieure au maquettage, ce qui est un point favorable — il montre une
> démarche itérative) et § 12 sur le développement front-end.

---

## 4. RÉSOLU — Harmonisation du point de vente sur Chatou

Le rapport situait le cas d'application à Chatou tandis que l'application
affichait Nanterre sur chaque écran : le jury aurait relevé l'écart en ouvrant la
solution. **Le code a été aligné sur le rapport**, qui fait foi puisqu'il
s'appuie sur l'entretien mené sur le terrain.

| | Avant | Après |
|---|---|---|
| Nom du point de vente | Nanterre | **Chatou** |
| Comptes de démonstration | `…@pdv-nanterre.fr` | **`…@pdv-chatou.fr`** |
| README, formulaire de connexion, jeu de test, export SQL | Nanterre | **Chatou** |

Mot de passe (`motdepasse123`), rôles et matrice d'accès inchangés.

**Côté rapport, il ne reste qu'à vérifier** qu'aucune occurrence de « Nanterre »
ne subsiste dans le document, et que les captures de l'annexe 2 sont bien les
versions régénérées (les précédentes affichaient l'ancien nom).

> ⚠️ **Action restante côté production** : la base en ligne conserve les données
> créées avant le renommage. Après déploiement, se connecter en Manager et
> utiliser « Réinitialiser les données de démonstration » pour que l'application
> déployée affiche Chatou.

---

## 5. Points déjà cohérents — ne rien changer

- Le rapport **ne cite aucun nombre de tests** : il ne périme pas quand la suite
  s'étoffe. Bonne pratique, à conserver.
- Le modèle à **sept tables** correspond exactement au code.
- § 10.8 (table `vente`), § 10.5 (source unique de vérité du chiffre d'affaires),
  la couche décision (alertes, prévision) : conformes à l'implémentation.
- Les captures de l'annexe 2 correspondent aux écrans actuels.
