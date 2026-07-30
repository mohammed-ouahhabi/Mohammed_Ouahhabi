# Présentation de soutenance — écarts avec l'application livrée

> Établi en confrontant `OUAHHABI_MOHAMED_PREZ1.pdf` (15 diapositives) à l'état
> réel du code. La présentation est bonne : structure claire, rythme maîtrisé,
> verbatim terrain, chiffres vérifiables. Restent **deux erreurs factuelles**,
> **un manque** et **un point de vigilance**.

---

## 1. ERREUR — Diapositive 08 : « Sept tables »

Le titre annonce *« Sept tables, une seule vérité pour le chiffre d'affaires »*.
Le modèle en compte désormais **huit** : `import_temporaire` a été ajoutée lors
de la correction du stockage des fichiers pendant l'import.

**Corriger le titre :**

> Huit tables, une seule vérité pour le chiffre d'affaires

**Ajouter la table au schéma**, à côté de `import_fichier` (elles relèvent toutes
deux du domaine « import ») :

```
import_temporaire
```

Si tu préfères ne pas surcharger le visuel, une alternative honnête consiste à
n'afficher que les **sept tables métier** et à préciser en légende :

> Sept tables métier, plus une table technique de dépôt temporaire des fichiers.

C'est même une meilleure lecture : elle distingue le modèle métier de
l'infrastructure. Choisis l'une des deux formulations, mais ne laisse pas
« sept » sans nuance.

---

## 2. ERREUR — Diapositive 09 : répartition des anomalies

Le bloc rouge indique :

| Affiché | Réel |
|---|---|
| 3 manquantes | 3 manquantes ✅ |
| **2 doublons** | **1 doublon** ❌ |
| **2 dates** | **3 dates** ❌ |
| 2 quantités | 2 quantités ✅ |
| 2 montants | 2 montants ✅ |

Le total (11) est juste, mais deux lignes sont inversées. Un jury qui lance le
fichier de démonstration verra l'écart à l'écran.

**Répartition à afficher :**

```
3 manquantes
1 doublon
3 dates
2 quantités
2 montants
```

---

## 3. MANQUE — L'écran « Opportunités promotionnelles »

C'est l'omission la plus importante : la troisième brique décisionnelle, ajoutée
après la conception de la présentation, n'apparaît nulle part. Or c'est celle qui
répond le mieux à la promesse du titre — *« une plateforme pour décider »*.

Deux façons de l'intégrer.

### Option A — L'ajouter à la diapositive 06 (recommandée)

La diapositive « CONSOLIDER → FIABILISER → ANTICIPER » devient un quatrième
temps :

> **1 CONSOLIDER** → **2 FIABILISER** → **3 ANTICIPER** → **4 AGIR**
>
> 4. AGIR — *Des actions commerciales chiffrées*

Et la phrase de bas de page :

> Une même chaîne : source → contrôle → indicateur → **action**

### Option B — Une diapositive dédiée, après la 11

Elle s'inscrirait dans la série « DÉMONSTRATION », dans le même gabarit que les
précédentes.

**Titre :** DÉMONSTRATION 4
**Accroche :** *La plateforme ne se contente pas de constater, elle propose*

**Trois colonnes, une par question :**

| QUAND | QUOI | COMMENT |
|---|---|---|
| Créneaux en retrait | Produits en retrait | Produits associés |
| 16h–17h : −71 % | Tiramisu : 3,3 % du CA | Pepperoni + Reine |
| 6 534 € de manque à gagner | contre 12,5 % en moyenne | panier **+19,74 €** |

**Phrase de bas de page :**

> Des règles explicites, pas un modèle opaque : chaque recommandation se justifie.

> **Le chiffre à mettre en avant, c'est `+19,74 €`.** Il dit qu'une association
> déjà choisie spontanément par les clients fait monter le ticket de vingt euros.
> C'est l'argument le plus concret de toute la présentation : une décision
> commerciale immédiate, appuyée sur une donnée mesurée.

---

## 4. VIGILANCE — Diapositive 11 : une alerte figée

La diapositive affiche : *« Pic d'activité à 18h — 5 commandes, +67 % au-dessus de
l'habitude »*.

Ce chiffre provient d'un jeu de données de démonstration **régénéré à chaque
réinitialisation**. Le jour de la soutenance, l'application affichera très
probablement une autre alerte : une chute de chiffre d'affaires, un autre
créneau, un autre pourcentage. L'écart entre ta diapositive et ton écran serait
relevé.

**Deux solutions :**

- **La plus sûre** — remplacer la valeur par la *règle* :
  > Pic d'activité — un créneau dépassant de plus de 50 % son habitude
- **Sinon** — refaire la capture juste avant la soutenance, une fois les données
  réinitialisées, et reporter la valeur réellement affichée.

La même prudence vaut pour « −30 % Produit en recul » : c'est le **seuil** de la
règle, ce qui est correct — ne le remplace pas par une valeur observée.

---

## 5. Points déjà justes — ne rien changer

- **Chatou (78)** : cohérent avec le rapport et l'application corrigée.
- **Diapositive 09** : 186 / 186 / 0, 25 / 14 / 11, 20 / 20 / 0 — tous exacts.
- **Diapositive 10** : 12 234 lignes, 5 370 commandes, 32 produits, 11 s → ≈ 5 s —
  tous vérifiés.
- **Diapositive 07** : les cinq étapes du pipeline correspondent au code.
- **Diapositive 08** : « CA calculé exclusivement depuis `ligne_commande` » —
  exact, et c'est un bon point à défendre.
- **Diapositive 12** : « Streamlit écarté » — bien vu, le jury peut poser la
  question.
- **Diapositive 15** : les limites assumées sont justes et bien formulées.

Le déroulé en cinq temps (Terrain → Réponse → Preuves → Maîtrise → Recul) est
solide : il fait passer la démonstration technique par le besoin métier, ce qui
est exactement ce qu'un jury attend.
