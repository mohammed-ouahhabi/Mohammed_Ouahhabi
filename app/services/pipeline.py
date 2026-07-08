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
import re
import unicodedata
from datetime import datetime

import pandas as pd
from sqlalchemy import func

from ..extensions import db
from ..models import Commande, LigneCommande, Produit, ImportFichier

# Champs du schéma cible (entrepôt) et leurs libellés d'affichage.
CHAMPS_CIBLE = ["date", "produit", "quantite", "montant"]
LIBELLES_CHAMPS = {
    "date": "Date",
    "produit": "Produit",
    "quantite": "Quantité",
    "montant": "Montant",
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
    },
    "quantite": {
        "quantite", "quantites", "qte", "qty", "quantity", "nombre", "nb",
        "volume",
    },
    "montant": {
        "montant", "montants", "prix", "amount", "total", "ca",
        "chiffreaffaires", "montantttc", "prixtotal", "montanteuros", "valeur",
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


class ErreurFichier(Exception):
    """Levée quand le fichier est structurellement invalide (illisible, ou aucune
    correspondance possible) : l'import ne peut pas démarrer."""


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

    auto = {}
    for champ in CHAMPS_CIBLE:
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

    manquantes = [src for src in mapping.values() if src not in df.columns]
    if manquantes:
        raise ErreurFichier(
            "Colonnes introuvables dans le fichier : " + ", ".join(manquantes) + "."
        )

    # Renomme colonne_source -> champ_cible, puis ne garde que les 4 colonnes.
    inverse = {mapping[champ]: champ for champ in CHAMPS_CIBLE}
    df = df.rename(columns=inverse)
    return df[CHAMPS_CIBLE].copy()


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

    for _, row in df.iterrows():
        date_val = _parser_date(row["date"])
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

        lignes_valides.append(
            {"date": date_val, "produit": produit, "quantite": quantite, "montant": montant}
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


def _produit_ou_creer(cache, nom):
    """Récupère un produit par nom (insensible à la casse) ou le crée."""
    cle = nom.lower()
    if cle in cache:
        return cache[cle]
    produit = Produit.query.filter(func.lower(Produit.nom) == cle).first()
    if produit is None:
        produit = Produit(nom=nom, categorie=None, prix_unitaire=0)
        db.session.add(produit)
        db.session.flush()  # obtient l'id sans commit complet
    cache[cle] = produit
    return produit


def integrer(lignes_valides, point_de_vente_id):
    """Étape 3 : insertion en base des lignes valides.

    Regroupe les lignes par horodatage en commandes, crée les produits manquants,
    puis insère les lignes de commande. Renvoie le nombre de lignes intégrées.
    """
    cache_produits = {}
    commandes = {}  # date_heure -> Commande

    for ligne in lignes_valides:
        produit = _produit_ou_creer(cache_produits, ligne["produit"])

        cle_cmd = ligne["date"]
        commande = commandes.get(cle_cmd)
        if commande is None:
            commande = Commande(
                point_de_vente_id=point_de_vente_id,
                date_heure=ligne["date"],
                montant_total=0,
            )
            db.session.add(commande)
            db.session.flush()
            commandes[cle_cmd] = commande

        commande.lignes.append(
            LigneCommande(
                produit_id=produit.id_produit,
                quantite=ligne["quantite"],
                montant=ligne["montant"],
            )
        )
        commande.montant_total = float(commande.montant_total or 0) + ligne["montant"]

    db.session.commit()
    return len(lignes_valides)


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

    # Étape 3 : intégration
    lignes_integrees = integrer(lignes_valides, point_de_vente_id)
    rapport["lignes_integrees"] = lignes_integrees

    # Journalisation de l'import (table import_fichier)
    statut = "termine" if lignes_integrees > 0 else "echec"
    enregistrement = ImportFichier(
        utilisateur_id=utilisateur.id_utilisateur,
        nom_fichier=nom_fichier,
        lignes_lues=rapport["lignes_lues"],
        lignes_rejetees=rapport["lignes_rejetees"],
        statut=statut,
    )
    db.session.add(enregistrement)
    db.session.commit()

    rapport["statut"] = statut
    rapport["nom_fichier"] = nom_fichier
    return rapport
