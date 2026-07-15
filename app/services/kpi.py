"""Calcul des indicateurs (KPI) du tableau de bord et de l'analyse des ventes.

Les formules suivent le cahier des charges :
    CA          = somme des montants des lignes de commande
    Commandes   = nombre de commandes
    Panier moyen= CA / nombre de commandes
    Produits vendus = somme des quantités
    Top produits    = regroupement par produit (quantité, CA)
    Pics d'activité = regroupement des commandes par heure

Tout est calculé côté base via SQLAlchemy (agrégations SQL) pour rester efficace
même avec beaucoup de lignes.
"""
from datetime import datetime, timedelta

from sqlalchemy import func

from ..extensions import db
from ..models import Commande, LigneCommande, Produit, Vente


def _base_lignes(point_de_vente_id, debut=None, fin=None):
    """Requête de base : les lignes de commande d'un PDV sur une période."""
    q = (
        db.session.query(LigneCommande)
        .join(Commande, LigneCommande.commande_id == Commande.id_commande)
        .filter(Commande.point_de_vente_id == point_de_vente_id)
    )
    if debut is not None:
        q = q.filter(Commande.date_heure >= debut)
    if fin is not None:
        q = q.filter(Commande.date_heure < fin)
    return q


def _base_commandes(point_de_vente_id, debut=None, fin=None):
    q = db.session.query(Commande).filter(
        Commande.point_de_vente_id == point_de_vente_id
    )
    if debut is not None:
        q = q.filter(Commande.date_heure >= debut)
    if fin is not None:
        q = q.filter(Commande.date_heure < fin)
    return q


def chiffre_affaires(point_de_vente_id, debut=None, fin=None):
    total = (
        _base_lignes(point_de_vente_id, debut, fin)
        .with_entities(func.coalesce(func.sum(LigneCommande.montant), 0))
        .scalar()
    )
    return float(total or 0)


def nombre_commandes(point_de_vente_id, debut=None, fin=None):
    return _base_commandes(point_de_vente_id, debut, fin).count()


def produits_vendus(point_de_vente_id, debut=None, fin=None):
    total = (
        _base_lignes(point_de_vente_id, debut, fin)
        .with_entities(func.coalesce(func.sum(LigneCommande.quantite), 0))
        .scalar()
    )
    return int(total or 0)


def panier_moyen(point_de_vente_id, debut=None, fin=None):
    nb = nombre_commandes(point_de_vente_id, debut, fin)
    if nb == 0:
        return 0.0
    return chiffre_affaires(point_de_vente_id, debut, fin) / nb


def top_produits(point_de_vente_id, debut=None, fin=None, limite=5):
    """Top produits par quantité vendue, avec CA associé."""
    lignes = (
        _base_lignes(point_de_vente_id, debut, fin)
        .join(Produit, LigneCommande.produit_id == Produit.id_produit)
        .with_entities(
            Produit.nom.label("nom"),
            func.sum(LigneCommande.quantite).label("quantite"),
            func.sum(LigneCommande.montant).label("ca"),
        )
        .group_by(Produit.id_produit, Produit.nom)
        .order_by(func.sum(LigneCommande.quantite).desc())
        .limit(limite)
        .all()
    )
    return [
        {"nom": r.nom, "quantite": int(r.quantite or 0), "ca": float(r.ca or 0)}
        for r in lignes
    ]


def detail_par_produit(point_de_vente_id, debut=None, fin=None, categorie=None, produit_id=None):
    """Tableau détaillé (analyse des ventes) : quantité, CA et part (%) par produit."""
    q = (
        _base_lignes(point_de_vente_id, debut, fin)
        .join(Produit, LigneCommande.produit_id == Produit.id_produit)
    )
    if categorie:
        q = q.filter(Produit.categorie == categorie)
    if produit_id:
        q = q.filter(Produit.id_produit == produit_id)

    lignes = (
        q.with_entities(
            Produit.nom.label("nom"),
            func.sum(LigneCommande.quantite).label("quantite"),
            func.sum(LigneCommande.montant).label("ca"),
        )
        .group_by(Produit.id_produit, Produit.nom)
        .order_by(func.sum(LigneCommande.montant).desc())
        .all()
    )
    ca_total = sum(float(r.ca or 0) for r in lignes) or 1.0  # évite la division par 0
    return [
        {
            "nom": r.nom,
            "quantite": int(r.quantite or 0),
            "ca": float(r.ca or 0),
            "part": round(float(r.ca or 0) / ca_total * 100),
        }
        for r in lignes
    ]


def repartition_paiements(point_de_vente_id, debut=None, fin=None, categorie=None, produit_id=None):
    """Montant encaissé par mode de paiement (table `vente`), sur la période.

    N'entre PAS dans le calcul du CA (toujours issu de ligne_commande) : il s'agit
    seulement de montrer la ventilation des encaissements. Les ventes sans mode de
    paiement renseigné sont ignorées.
    """
    q = (
        db.session.query(
            Vente.mode_paiement.label("mode"),
            func.coalesce(func.sum(Vente.montant), 0).label("montant"),
        )
        .join(Commande, Vente.commande_id == Commande.id_commande)
        .filter(Commande.point_de_vente_id == point_de_vente_id)
        .filter(Vente.mode_paiement.isnot(None))
    )
    if debut is not None:
        q = q.filter(Commande.date_heure >= debut)
    if fin is not None:
        q = q.filter(Commande.date_heure < fin)

    # Filtres produit / catégorie : on restreint aux commandes concernées
    # (le mode de paiement est une propriété du ticket, pas du produit).
    if categorie or produit_id:
        sous_requete = db.session.query(LigneCommande.commande_id).join(
            Produit, LigneCommande.produit_id == Produit.id_produit
        )
        if categorie:
            sous_requete = sous_requete.filter(Produit.categorie == categorie)
        if produit_id:
            sous_requete = sous_requete.filter(Produit.id_produit == produit_id)
        q = q.filter(Commande.id_commande.in_(sous_requete))

    lignes = (
        q.group_by(Vente.mode_paiement)
        .order_by(func.sum(Vente.montant).desc())
        .all()
    )
    return [{"mode": r.mode, "montant": float(r.montant or 0)} for r in lignes if r.mode]


def pics_activite(point_de_vente_id, debut=None, fin=None):
    """Nombre de commandes par heure de la journée (0 à 23).

    On récupère toutes les commandes de la période et on regroupe en Python par
    heure : c'est portable entre SQLite et PostgreSQL (extraction d'heure SQL
    diffère d'un moteur à l'autre) et le volume par période reste raisonnable.
    """
    commandes = (
        _base_commandes(point_de_vente_id, debut, fin)
        .with_entities(Commande.date_heure)
        .all()
    )
    par_heure = {h: 0 for h in range(24)}
    for (dh,) in commandes:
        if dh is not None:
            par_heure[dh.hour] += 1
    return par_heure


def evolution_ca(point_de_vente_id, debut, fin):
    """CA agrégé par jour sur la période (pour le graphique d'évolution)."""
    lignes = (
        _base_lignes(point_de_vente_id, debut, fin)
        .with_entities(Commande.date_heure, LigneCommande.montant)
        .all()
    )
    par_jour = {}
    for dh, montant in lignes:
        if dh is None:
            continue
        cle = dh.date()
        par_jour[cle] = par_jour.get(cle, 0.0) + float(montant or 0)
    jours = sorted(par_jour.keys())
    return {
        "labels": [j.strftime("%d/%m") for j in jours],
        "valeurs": [round(par_jour[j], 2) for j in jours],
    }


def ventes_par_periode(point_de_vente_id, debut, fin):
    """CA par jour, pour le graphique en barres « Ventes par période »."""
    evo = evolution_ca(point_de_vente_id, debut, fin)
    return evo


# --------------------------------------------------------------------------
# Regroupement pratique pour le tableau de bord
# --------------------------------------------------------------------------
def resume_dashboard(point_de_vente_id, jours=30):
    """Renvoie tous les indicateurs du tableau de bord, période courante vs
    période précédente (pour afficher les variations « +8 % » de la maquette)."""
    fin = _maintenant()
    debut = fin - timedelta(days=jours)
    debut_prec = debut - timedelta(days=jours)

    ca = chiffre_affaires(point_de_vente_id, debut, fin)
    ca_prec = chiffre_affaires(point_de_vente_id, debut_prec, debut)
    nb = nombre_commandes(point_de_vente_id, debut, fin)
    nb_prec = nombre_commandes(point_de_vente_id, debut_prec, debut)
    pv = produits_vendus(point_de_vente_id, debut, fin)
    pv_prec = produits_vendus(point_de_vente_id, debut_prec, debut)
    pm = panier_moyen(point_de_vente_id, debut, fin)
    pm_prec = panier_moyen(point_de_vente_id, debut_prec, debut)

    return {
        "periode": {"debut": debut, "fin": fin, "jours": jours},
        "ca": ca,
        "ca_variation": _variation(ca, ca_prec),
        "commandes": nb,
        "commandes_variation": _variation(nb, nb_prec),
        "panier_moyen": pm,
        "panier_moyen_variation": _variation(pm, pm_prec),
        "produits_vendus": pv,
        "produits_vendus_variation": _variation(pv, pv_prec),
        "top_produits": top_produits(point_de_vente_id, debut, fin),
        "pics_activite": pics_activite(point_de_vente_id, debut, fin),
        "evolution_ca": evolution_ca(point_de_vente_id, debut, fin),
    }


def _variation(courant, precedent):
    """Variation en % entre deux valeurs (None si la précédente est nulle)."""
    if not precedent:
        return None
    return round((courant - precedent) / precedent * 100)


def _maintenant():
    # Isolé dans une fonction pour être facilement remplaçable dans les tests.
    return datetime.utcnow()
