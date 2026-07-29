"""Pipeline d'import d'un fichier CSV de ventes (brique « data engineer »).

Objectif : rendre le traitement VISIBLE et VÉRIFIABLE, et l'ouvrir à n'importe
quel magasin. La source est libre (les colonnes peuvent porter des noms
différents d'un point de vente à l'autre) ; une **couche de correspondance**
(mapping) normalise le fichier vers le schéma d'entrepôt attendu.

Étapes (cf. maquette « Import de données ») :

    0. Détection des colonnes -> auto-correspondance via un dictionnaire d'alias
    1. Fichier reçu           -> lecture pandas selon la correspondance choisie
    2. Contrôles qualité      -> doublons, valeurs manquantes, formats incohérents
    3. Intégration entrepôt   -> insertion des lignes valides via SQLAlchemy
    4. Mise à jour KPI        -> automatique (les KPI sont recalculés depuis la base)

Schéma cible (entrepôt) : `date, produit, quantite, montant`. Ce n'est pas une
contrainte de nommage imposée à la source, c'est le minimum vital pour calculer
les KPI. La source, elle, peut nommer ses colonnes comme elle veut.

Regroupement en commandes : les lignes portant le même horodatage (`date`) sont
considérées comme un même ticket et regroupées dans une seule `commande`.
"""
import hashlib
import re
import unicodedata
from datetime import datetime

import pandas as pd
from sqlalchemy import func

from ..extensions import db
from ..models import Commande, LigneCommande, Produit, ImportFichier, Vente

# Champs du schéma cible (entrepôt) et leurs libellés d'affichage.
CHAMPS_CIBLE = ["date", "produit", "quantite", "montant"]
# Champs facultatifs : mappés s'ils sont présents, ignorés sinon (pas d'erreur).
CHAMPS_OPTIONNELS = ["heure", "mode_paiement"]
LIBELLES_CHAMPS = {
    "date": "Date",
    "produit": "Produit",
    "quantite": "Quantité",
    "montant": "Montant",
    "heure": "Heure (si séparée de la date)",
    "mode_paiement": "Mode de paiement",
}
# Rétro-compatibilité (ancien nom de la constante).
COLONNES_ATTENDUES = CHAMPS_CIBLE

# Dictionnaire d'alias : pour chaque champ cible, les noms de colonnes source
# reconnus automatiquement (déjà normalisés : sans accent, minuscules, sans
# espaces ni séparateurs). Facile à enrichir quand un nouveau format apparaît.
ALIAS = {
    "date": {
        "date", "dateheure", "datecommande", "datevente", "orderdate",
        "jour", "horodatage", "timestamp", "datetime", "dateticket",
    },
    "produit": {
        "produit", "produits", "article", "item", "product", "libelle",
        "designation", "nomproduit", "pizza", "reference",
        "nompizza", "nomarticle", "designationproduit",
    },
    "quantite": {
        "quantite", "quantites", "qte", "qty", "quantity", "nombre", "nb",
        "volume", "nbarticles",
    },
    "montant": {
        "montant", "montants", "prix", "amount", "total", "ca",
        "chiffreaffaires", "montantttc", "prixtotal", "montanteuros", "valeur",
        "totalligne", "montantligne",
    },
    # Colonne d'heure séparée : fréquente dans les exports de caisse, où la date
    # et l'heure figurent dans deux colonnes distinctes.
    "heure": {
        "heure", "heurecommande", "heurevente", "time", "ordertime",
        "heureticket", "horaire",
    },
    "mode_paiement": {
        "modepaiement", "paiement", "reglement", "payment", "paymentmethod",
        "moyenpaiement",
    },
}

# Formats de date acceptés à la lecture.
FORMATS_DATE = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
]

# Formats acceptés pour une colonne d'heure séparée.
FORMATS_HEURE = ["%H:%M:%S", "%H:%M"]


class ErreurFichier(Exception):
    """Levée quand le fichier est structurellement invalide (illisible, ou aucune
    correspondance possible) : l'import ne peut pas démarrer."""


# --------------------------------------------------------------------------
# Idempotence — garantir qu'une même donnée ne peut pas être intégrée deux fois
# --------------------------------------------------------------------------
# Deux couches complémentaires :
#   a) empreinte du FICHIER  : détecte un réimport à l'identique (avertissement) ;
#   b) clé par LIGNE         : la couche robuste, qui couvre aussi le cas d'un
#      fichier mêlant des lignes déjà vues et des lignes nouvelles.
# Sans cela, réimporter un fichier gonfle mécaniquement le chiffre d'affaires.

def calculer_hash_fichier(chemin):
    """Empreinte SHA-256 du contenu du fichier (lecture par blocs)."""
    sha = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            sha.update(bloc)
    return sha.hexdigest()


def cle_ligne(date, produit, quantite, montant):
    """Clé d'idempotence déterministe d'une ligne de vente.

    Construite sur les données métier de la ligne : date + produit normalisé
    (sans accent ni casse) + quantité + montant arrondi. Deux lignes identiques
    issues de deux fichiers différents produisent la même clé.
    """
    empreinte = "|".join([
        date.isoformat(),
        _sans_accents(produit),
        str(int(quantite)),
        f"{float(montant):.2f}",
    ])
    return hashlib.sha256(empreinte.encode("utf-8")).hexdigest()


def import_precedent(hash_fichier):
    """Renvoie le dernier import RÉUSSI portant la même empreinte, sinon None."""
    if not hash_fichier:
        return None
    return (
        ImportFichier.query.filter_by(hash_fichier=hash_fichier, statut="termine")
        .order_by(ImportFichier.date_import.desc())
        .first()
    )


def _cles_deja_presentes(cles):
    """Sous-ensemble des clés déjà présentes dans l'entrepôt.

    Requête par lots pour rester compatible avec les limites de paramètres de
    SQLite comme de PostgreSQL.
    """
    presentes = set()
    cles = list(cles)
    for debut in range(0, len(cles), 500):
        lot = cles[debut:debut + 500]
        trouvees = (
            db.session.query(LigneCommande.cle_idempotence)
            .filter(LigneCommande.cle_idempotence.in_(lot))
            .all()
        )
        presentes.update(c[0] for c in trouvees)
    return presentes


def _sans_accents(texte):
    texte = unicodedata.normalize("NFKD", str(texte))
    return "".join(c for c in texte if not unicodedata.combining(c)).strip().lower()


def _cle(texte):
    """Normalise un en-tête pour la comparaison : sans accent, minuscule, et sans
    espaces / underscores / tirets. « Date Commande » et « date_commande » ->
    « datecommande »."""
    return re.sub(r"[\s_\-.]+", "", _sans_accents(texte))


def _lire_csv(chemin, nrows=None):
    """Lit le CSV (séparateur auto-détecté) en gardant tout en texte : on parse
    et on valide nous-mêmes, colonne par colonne, dans les contrôles qualité."""
    try:
        return pd.read_csv(chemin, sep=None, engine="python", nrows=nrows, dtype=str)
    except Exception as exc:  # fichier corrompu, binaire, vide...
        raise ErreurFichier(
            "Le fichier n'a pas pu être lu comme un CSV valide."
        ) from exc


def detecter_colonnes(chemin):
    """Étape 0 : lit les en-têtes et propose une correspondance automatique.

    Renvoie un dictionnaire :
        {
          "colonnes": [noms réels des colonnes du fichier],
          "auto":     {champ_cible: colonne_source ou None},
          "apercu":   [3 premières lignes, pour aider l'utilisateur à mapper],
        }
    """
    df = _lire_csv(chemin, nrows=5)
    colonnes = [str(c) for c in df.columns]
    cles = {col: _cle(col) for col in colonnes}

    # Auto-correspondance des champs obligatoires ET facultatifs.
    auto = {}
    for champ in CHAMPS_CIBLE + CHAMPS_OPTIONNELS:
        trouve = None
        for col in colonnes:
            if cles[col] in ALIAS[champ]:
                trouve = col
                break
        auto[champ] = trouve

    apercu = df.head(3).fillna("").astype(str).to_dict(orient="records")
    return {"colonnes": colonnes, "auto": auto, "apercu": apercu}


def mapping_complet(mapping):
    """Vrai si les 4 champs cibles sont associés à une colonne source."""
    return all(mapping.get(c) for c in CHAMPS_CIBLE)


def lire_avec_mapping(chemin, mapping):
    """Étape 1 : lit le fichier et renomme les colonnes source vers le schéma cible.

    `mapping` : {champ_cible: nom_de_colonne_dans_le_fichier}.
    Lève ErreurFichier si la correspondance est incomplète ou si une colonne
    annoncée n'existe pas dans le fichier.
    """
    if not mapping_complet(mapping):
        manquants = [LIBELLES_CHAMPS[c] for c in CHAMPS_CIBLE if not mapping.get(c)]
        raise ErreurFichier(
            "Champs non renseignés : " + ", ".join(manquants)
            + ". Associez chaque champ à une colonne du fichier."
        )

    df = _lire_csv(chemin)
    df.columns = [str(c) for c in df.columns]

    # Seules les colonnes des champs OBLIGATOIRES doivent exister.
    manquantes = [mapping[c] for c in CHAMPS_CIBLE if mapping[c] not in df.columns]
    if manquantes:
        raise ErreurFichier(
            "Colonnes introuvables dans le fichier : " + ", ".join(manquantes) + "."
        )

    # Une même colonne source ne peut pas alimenter deux champs obligatoires :
    # on le signale clairement plutôt que de laisser planter le traitement.
    doublons = [
        col for col in {mapping[c] for c in CHAMPS_CIBLE}
        if [mapping[c] for c in CHAMPS_CIBLE].count(col) > 1
    ]
    if doublons:
        raise ErreurFichier(
            "La colonne « " + doublons[0] + " » est associée à plusieurs champs. "
            "Chaque champ doit correspondre à une colonne différente."
        )

    # Renomme colonne_source -> champ_cible pour les champs obligatoires...
    inverse = {mapping[champ]: champ for champ in CHAMPS_CIBLE}
    colonnes_gardees = list(CHAMPS_CIBLE)
    utilisees = set(inverse)
    # ... puis pour les champs facultatifs réellement présents dans le fichier.
    # Un champ facultatif pointant vers une colonne déjà utilisée est ignoré :
    # l'information y est déjà lue (cas typique d'une colonne « date_heure »
    # choisie à la fois comme Date et comme Heure).
    for opt in CHAMPS_OPTIONNELS:
        src = mapping.get(opt)
        if src and src in df.columns and src not in utilisees:
            inverse[src] = opt
            utilisees.add(src)
            colonnes_gardees.append(opt)

    df = df.rename(columns=inverse)
    return df[colonnes_gardees].copy()


def lire_et_normaliser(chemin):
    """Lecture « automatique » : détecte les colonnes puis applique la
    correspondance auto. Pratique en ligne de commande / tests ; lève
    ErreurFichier si l'auto-détection ne couvre pas les 4 champs."""
    info = detecter_colonnes(chemin)
    return lire_avec_mapping(chemin, info["auto"])


def _parser_date(valeur):
    """Essaie plusieurs formats ; renvoie un datetime ou None si aucun ne marche."""
    if valeur is None:
        return None
    texte = str(valeur).strip()
    if texte == "" or texte.lower() == "nan":
        return None
    for fmt in FORMATS_DATE:
        try:
            return datetime.strptime(texte, fmt)
        except ValueError:
            continue
    return None


def _parser_heure(valeur):
    """Analyse une valeur d'heure isolée (HH:MM:SS ou HH:MM). None si invalide."""
    if valeur is None:
        return None
    texte = str(valeur).strip()
    if texte == "" or texte.lower() == "nan":
        return None
    for fmt in FORMATS_HEURE:
        try:
            return datetime.strptime(texte, fmt).time()
        except ValueError:
            continue
    return None


def _horodatage(valeur_date, valeur_heure=None):
    """Recompose un horodatage à partir d'une date et, si besoin, d'une heure.

    Beaucoup d'exports de caisse séparent la date (`2026-01-01`) et l'heure
    (`11:38:36`) en deux colonnes. Sans recomposition, toutes les ventes d'une
    même journée porteraient le même horodatage et seraient regroupées en une
    seule commande — faussant le nombre de commandes, le panier moyen et les
    pics horaires.

    Règles :
      - si la colonne date porte déjà une heure, elle fait foi (pas de double
        heure) ;
      - si l'heure est absente ou invalide, on conserve la date seule : l'heure
        est une précision, pas une condition de validité.
    """
    base = _parser_date(valeur_date)
    if base is None:
        return None
    # La présence de « : » signale que la date embarque déjà une heure.
    if ":" in str(valeur_date):
        return base
    heure = _parser_heure(valeur_heure)
    if heure is None:
        return base
    return base.replace(hour=heure.hour, minute=heure.minute, second=heure.second)


def controler_qualite(df):
    """Étape 2 : contrôles qualité ligne à ligne.

    Sépare les lignes valides des lignes rejetées et détaille les anomalies.
    Renvoie (df_valides, rapport_qualite).
    """
    total = len(df)
    anomalies = {
        "valeurs_manquantes": 0,
        "doublons": 0,
        "format_date": 0,
        "quantite_invalide": 0,
        "montant_invalide": 0,
    }

    lignes_valides = []
    vus = set()  # pour détecter les doublons (date, produit, quantite, montant)
    a_mode_paiement = "mode_paiement" in df.columns
    a_heure = "heure" in df.columns

    for _, row in df.iterrows():
        # Horodatage : recomposé si l'heure est fournie dans une colonne séparée.
        date_val = _horodatage(row["date"], row["heure"] if a_heure else None)
        produit = str(row["produit"]).strip() if pd.notna(row["produit"]) else ""

        # a) valeurs manquantes
        if produit == "" or pd.isna(row["quantite"]) or pd.isna(row["montant"]) or pd.isna(row["date"]):
            anomalies["valeurs_manquantes"] += 1
            continue

        # b) format de date
        if date_val is None:
            anomalies["format_date"] += 1
            continue

        # c) quantité entière positive
        try:
            quantite = int(float(row["quantite"]))
            if quantite <= 0:
                raise ValueError
        except (ValueError, TypeError):
            anomalies["quantite_invalide"] += 1
            continue

        # d) montant numérique positif
        try:
            montant = float(str(row["montant"]).replace(",", "."))
            if montant < 0:
                raise ValueError
        except (ValueError, TypeError):
            anomalies["montant_invalide"] += 1
            continue

        # e) doublons
        cle = (date_val.isoformat(), produit.lower(), quantite, round(montant, 2))
        if cle in vus:
            anomalies["doublons"] += 1
            continue
        vus.add(cle)

        # Champ facultatif : mode de paiement (rattaché à la commande à l'intégration).
        mode = None
        if a_mode_paiement and pd.notna(row["mode_paiement"]):
            mode = str(row["mode_paiement"]).strip() or None

        lignes_valides.append(
            {
                "date": date_val,
                "produit": produit,
                "quantite": quantite,
                "montant": montant,
                "mode_paiement": mode,
            }
        )

    rejetees = total - len(lignes_valides)
    rapport = {
        "lignes_lues": total,
        "lignes_valides": len(lignes_valides),
        "lignes_rejetees": rejetees,
        "anomalies": anomalies,
        "anomalie_principale": _anomalie_principale(anomalies),
    }
    return lignes_valides, rapport


def _anomalie_principale(anomalies):
    """Libellé de l'anomalie la plus fréquente (affiché dans le récapitulatif)."""
    libelles = {
        "valeurs_manquantes": "Valeurs manquantes",
        "doublons": "Doublons",
        "format_date": "Formats de date",
        "quantite_invalide": "Quantités invalides",
        "montant_invalide": "Montants invalides",
    }
    principale = max(anomalies, key=anomalies.get)
    if anomalies[principale] == 0:
        return "Aucune"
    return libelles[principale]


def _resoudre_produits(noms):
    """Récupère (ou crée) tous les produits en une seule passe.

    Résoudre les produits en amont évite une requête par ligne : sur un fichier
    de plusieurs milliers de lignes, la différence est décisive.
    Renvoie un dictionnaire {nom en minuscules: Produit}.
    """
    cache = {}
    voulus = {nom.lower(): nom for nom in noms}
    if not voulus:
        return cache

    existants = (
        Produit.query.filter(func.lower(Produit.nom).in_(list(voulus))).all()
    )
    for produit in existants:
        cache[produit.nom.lower()] = produit

    manquants = [nom for cle, nom in voulus.items() if cle not in cache]
    for nom in manquants:
        produit = Produit(nom=nom, categorie=None, prix_unitaire=0)
        db.session.add(produit)
        cache[nom.lower()] = produit
    if manquants:
        db.session.flush()  # attribue les identifiants des nouveaux produits
    return cache


def integrer(lignes_valides, point_de_vente_id):
    """Étape 3 : insertion en base des lignes valides, de façon IDEMPOTENTE.

    Chaque ligne porte une clé déterministe : celles qui existent déjà dans
    l'entrepôt sont ignorées (jamais réinsérées), ce qui rend l'import rejouable
    sans gonfler les indicateurs. Les commandes ne sont créées que pour les
    lignes réellement nouvelles.

    Renvoie le couple (lignes_intégrées, lignes_ignorées).
    """
    # 1. Clé de chaque ligne + dédoublonnage à l'intérieur du lot.
    a_traiter, vues_dans_le_lot, ignorees = [], set(), 0
    for ligne in lignes_valides:
        cle = cle_ligne(ligne["date"], ligne["produit"], ligne["quantite"], ligne["montant"])
        if cle in vues_dans_le_lot:
            ignorees += 1
            continue
        vues_dans_le_lot.add(cle)
        a_traiter.append((cle, ligne))

    # 2. Écarte les lignes déjà présentes en base (imports précédents).
    deja = _cles_deja_presentes(cle for cle, _ in a_traiter)
    nouvelles = [(cle, ligne) for cle, ligne in a_traiter if cle not in deja]
    ignorees += len(a_traiter) - len(nouvelles)

    if not nouvelles:
        return 0, ignorees

    # 3. Résolution de tous les produits en amont (une seule requête).
    cache_produits = _resoudre_produits({ligne["produit"] for _, ligne in nouvelles})

    # 4. Construction des commandes, lignes et ventes.
    # On passe par les relations SQLAlchemy plutôt que par les identifiants :
    # aucun flush intermédiaire n'est nécessaire, tout part en un seul commit.
    commandes = {}  # date_heure -> Commande
    modes = {}      # date_heure -> mode de paiement retenu pour la commande

    for cle, ligne in nouvelles:
        produit = cache_produits[ligne["produit"].lower()]

        cle_cmd = ligne["date"]
        commande = commandes.get(cle_cmd)
        if commande is None:
            commande = Commande(
                point_de_vente_id=point_de_vente_id,
                date_heure=ligne["date"],
                montant_total=0,
            )
            db.session.add(commande)
            commandes[cle_cmd] = commande

        # Mode de paiement au niveau du ticket : on retient la 1re valeur non vide.
        if modes.get(cle_cmd) is None and ligne.get("mode_paiement"):
            modes[cle_cmd] = ligne["mode_paiement"]

        commande.lignes.append(
            LigneCommande(
                produit=produit,
                quantite=ligne["quantite"],
                montant=ligne["montant"],
                cle_idempotence=cle,
            )
        )
        commande.montant_total = float(commande.montant_total or 0) + ligne["montant"]

    # Une vente (encaissement) par commande — issue du système source Pulse.
    for cle_cmd, commande in commandes.items():
        db.session.add(
            Vente(
                commande=commande,
                montant=commande.montant_total,
                date_vente=commande.date_heure,
                mode_paiement=modes.get(cle_cmd),
            )
        )

    db.session.commit()
    return len(nouvelles), ignorees


def traiter_fichier(chemin, nom_fichier, utilisateur, point_de_vente_id, mapping=None):
    """Orchestration complète du pipeline, avec journalisation dans import_fichier.

    `mapping` : correspondance colonnes source -> champs cibles. Si None, on tente
    l'auto-détection (pratique pour les tests / la CLI).

    Renvoie un dictionnaire `rapport` consommé par le template. Lève ErreurFichier
    si le fichier est invalide.
    """
    # Étape 1 : lecture selon la correspondance
    if mapping is None:
        df = lire_et_normaliser(chemin)
    else:
        df = lire_avec_mapping(chemin, mapping)

    # Étape 2 : contrôles qualité
    lignes_valides, rapport = controler_qualite(df)

    # Étape 3 : intégration idempotente
    lignes_integrees, lignes_ignorees = integrer(lignes_valides, point_de_vente_id)
    rapport["lignes_integrees"] = lignes_integrees
    rapport["lignes_ignorees"] = lignes_ignorees

    # Journalisation de l'import (table import_fichier).
    # Un import qui n'apporte que des lignes déjà connues n'est pas un échec :
    # c'est un import correctement neutralisé par l'idempotence.
    statut = "termine" if (lignes_integrees > 0 or lignes_ignorees > 0) else "echec"
    enregistrement = ImportFichier(
        utilisateur_id=utilisateur.id_utilisateur,
        nom_fichier=nom_fichier,
        lignes_lues=rapport["lignes_lues"],
        lignes_rejetees=rapport["lignes_rejetees"],
        lignes_ignorees=lignes_ignorees,
        hash_fichier=calculer_hash_fichier(chemin),
        statut=statut,
    )
    db.session.add(enregistrement)
    db.session.commit()

    rapport["statut"] = statut
    rapport["nom_fichier"] = nom_fichier
    return rapport
