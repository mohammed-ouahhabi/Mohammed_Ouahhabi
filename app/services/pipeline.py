"""Pipeline d'import d'un fichier CSV de ventes (brique « data engineer »).

Objectif : rendre le traitement VISIBLE et VÉRIFIABLE. Chaque étape produit un
compte-rendu affiché à l'écran (cf. maquette « Import de données ») :

    1. Fichier reçu          -> lecture pandas, vérification des colonnes
    2. Contrôles qualité     -> doublons, valeurs manquantes, formats incohérents
    3. Intégration entrepôt  -> insertion des lignes valides via SQLAlchemy
    4. Mise à jour KPI       -> automatique (les KPI sont recalculés depuis la base)

Format attendu du CSV : colonnes `date, produit, quantite, montant`
(les accents et majuscules sur les en-têtes sont tolérés).

Regroupement en commandes : les lignes portant le même horodatage (`date`) sont
considérées comme un même ticket et regroupées dans une seule `commande`. Choix
assumé et explicable : sans identifiant de commande dans le fichier, l'instant
d'achat est le meilleur regroupement disponible.
"""
import unicodedata
from datetime import datetime

import pandas as pd
from sqlalchemy import func

from ..extensions import db
from ..models import Commande, LigneCommande, Produit, ImportFichier

COLONNES_ATTENDUES = ["date", "produit", "quantite", "montant"]

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
    """Levée quand le fichier est structurellement invalide (mauvais format,
    colonnes manquantes) : l'import ne peut pas démarrer."""


def _sans_accents(texte):
    texte = unicodedata.normalize("NFKD", str(texte))
    return "".join(c for c in texte if not unicodedata.combining(c)).strip().lower()


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


def lire_et_normaliser(chemin):
    """Étape 1 : lecture du CSV et vérification de la structure.

    Renvoie un DataFrame dont les colonnes sont renommées vers les noms attendus.
    Lève ErreurFichier si le fichier est illisible ou s'il manque des colonnes.
    """
    try:
        df = pd.read_csv(chemin, sep=None, engine="python")
    except Exception as exc:  # fichier corrompu, binaire, vide...
        raise ErreurFichier(
            "Le fichier n'a pas pu être lu comme un CSV valide."
        ) from exc

    # Fait correspondre les en-têtes réels (accents/majuscules tolérés) aux
    # noms attendus. « quantité » -> « quantite ».
    correspondances = {}
    for col in df.columns:
        cle = _sans_accents(col)
        if cle in COLONNES_ATTENDUES:
            correspondances[col] = cle
    df = df.rename(columns=correspondances)

    manquantes = [c for c in COLONNES_ATTENDUES if c not in df.columns]
    if manquantes:
        raise ErreurFichier(
            "Colonnes manquantes ou mal nommées : "
            + ", ".join(manquantes)
            + ". Colonnes attendues : date, produit, quantite, montant."
        )

    return df[COLONNES_ATTENDUES].copy()


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


def traiter_fichier(chemin, nom_fichier, utilisateur, point_de_vente_id):
    """Orchestration complète du pipeline, avec journalisation dans import_fichier.

    Renvoie un dictionnaire `rapport` consommé par le template pour afficher la
    timeline et le récapitulatif. Lève ErreurFichier si le fichier est invalide.
    """
    # Étapes 1 & 2
    df = lire_et_normaliser(chemin)
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
