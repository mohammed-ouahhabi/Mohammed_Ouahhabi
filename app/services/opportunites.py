"""Opportunités promotionnelles — couche « aide à la décision » (lecture seule).

Le tableau de bord dit ce qui s'est passé ; les alertes disent ce qui mérite
attention. Cette brique va un cran plus loin : elle propose **des actions
commerciales chiffrées**, dérivées des données déjà en base.

Trois analyses, toutes déterministes et explicables :

  1. Créneaux creux        -> QUAND placer une offre
  2. Produits en retrait   -> QUOI mettre en avant (ou retirer)
  3. Produits associés     -> QUELLES formules créer

Aucun apprentissage automatique : chaque recommandation se déduit d'une règle
que l'on peut énoncer en une phrase, et s'accompagne des chiffres qui la
justifient. C'est un choix assumé — une recommandation que l'on ne sait pas
expliquer n'est pas exploitable par un responsable de point de vente.

Le chiffre d'affaires n'est jamais recalculé ici : on réutilise services/kpi.py.
"""
from datetime import timedelta
from itertools import combinations

from sqlalchemy import func

from ..extensions import db
from ..models import Commande, LigneCommande, Produit
from . import kpi

# --- Seuils (ajustables) ---------------------------------------------------
HEURE_OUVERTURE = 11
HEURE_FERMETURE = 22
SEUIL_CRENEAU_CREUX = 0.60     # créneau sous 60 % de la moyenne horaire
MIN_COMMANDES_CRENEAU = 5      # en deçà, l'échantillon n'est pas significatif
SEUIL_PRODUIT_RETRAIT = 0.60   # produit sous 60 % de la part moyenne
MIN_VENTES_PRODUIT = 10        # en deçà, on ne conclut pas
MIN_COMMANDES_PAIRE = 10       # nombre mini d'occurrences d'une association
NB_PAIRES = 3                  # nombre d'associations proposées


def analyser(point_de_vente_id, jours=90):
    """Renvoie les opportunités détectées sur la période, prêtes à l'affichage."""
    fin = kpi._maintenant()
    debut = fin - timedelta(days=jours)

    creneaux = creneaux_creux(point_de_vente_id, debut, fin)
    retrait = produits_en_retrait(point_de_vente_id, debut, fin)
    return {
        "periode": {"debut": debut, "fin": fin, "jours": jours},
        "creneaux_creux": creneaux,
        "produits_en_retrait": retrait,
        "associations": associations_produits(point_de_vente_id, debut, fin),
        # Séries complètes, pour visualiser l'écart plutôt que de le lire.
        "graphe_heures": serie_ca_par_heure(point_de_vente_id, debut, fin),
        "graphe_produits": serie_parts_produits(point_de_vente_id, debut, fin, retrait),
    }


def serie_ca_par_heure(point_de_vente_id, debut, fin):
    """CA par heure sur la plage d'ouverture, en signalant les créneaux creux."""
    lignes = (
        db.session.query(Commande.date_heure, LigneCommande.montant)
        .join(LigneCommande, LigneCommande.commande_id == Commande.id_commande)
        .filter(Commande.point_de_vente_id == point_de_vente_id)
        .filter(Commande.date_heure >= debut, Commande.date_heure < fin)
        .all()
    )
    par_heure = {h: 0.0 for h in range(HEURE_OUVERTURE, HEURE_FERMETURE + 1)}
    for date_heure, montant in lignes:
        if date_heure.hour in par_heure:
            par_heure[date_heure.hour] += float(montant or 0)

    actifs = [v for v in par_heure.values() if v > 0]
    moyenne = sum(actifs) / len(actifs) if actifs else 0
    seuil = moyenne * SEUIL_CRENEAU_CREUX

    # Le graphique applique la règle annoncée dans son en-tête : *tout* créneau
    # sous le seuil est signalé. La liste détaillée sous le graphique ne retient
    # que les trois plus pénalisants — c'est un choix d'affichage, pas la règle.
    return {
        "labels": [f"{h}h" for h in sorted(par_heure)],
        "valeurs": [round(par_heure[h], 2) for h in sorted(par_heure)],
        "creux": [0 < par_heure[h] < seuil for h in sorted(par_heure)],
        "moyenne": round(moyenne, 2),
        "seuil": round(seuil, 2),
    }


def serie_parts_produits(point_de_vente_id, debut, fin, retrait):
    """Part de CA de chaque produit, en signalant ceux qui sont en retrait."""
    detail = kpi.detail_par_produit(point_de_vente_id, debut, fin)
    ca_total = sum(r["ca"] for r in detail)
    if ca_total <= 0:
        return {"labels": [], "valeurs": [], "faibles": [], "moyenne": 0}

    noms_retrait = {p["nom"] for p in retrait}
    detail = sorted(detail, key=lambda r: r["ca"], reverse=True)
    return {
        "labels": [r["nom"] for r in detail],
        "valeurs": [round(r["ca"] / ca_total * 100, 1) for r in detail],
        "faibles": [r["nom"] in noms_retrait for r in detail],
        "moyenne": round(100 / len(detail), 1),
    }


# --------------------------------------------------------------------------
# 1. Créneaux creux — quand placer une offre
# --------------------------------------------------------------------------
def creneaux_creux(point_de_vente_id, debut, fin):
    """Créneaux horaires dont le chiffre d'affaires est nettement sous la moyenne.

    Règle : sur la plage d'ouverture, un créneau dont le CA est inférieur à 60 %
    de la moyenne horaire est considéré comme creux. Le manque à gagner estimé
    est l'écart à cette moyenne — ce que rapporterait le créneau s'il se
    comportait comme les autres.
    """
    lignes = (
        db.session.query(Commande.date_heure, LigneCommande.montant)
        .join(LigneCommande, LigneCommande.commande_id == Commande.id_commande)
        .filter(Commande.point_de_vente_id == point_de_vente_id)
        .filter(Commande.date_heure >= debut, Commande.date_heure < fin)
        .all()
    )
    if not lignes:
        return []

    ca_par_heure = {h: 0.0 for h in range(HEURE_OUVERTURE, HEURE_FERMETURE + 1)}
    commandes_par_heure = {h: set() for h in ca_par_heure}
    for date_heure, montant in lignes:
        h = date_heure.hour
        if h in ca_par_heure:
            ca_par_heure[h] += float(montant or 0)
            commandes_par_heure[h].add(date_heure)

    actifs = {h: ca for h, ca in ca_par_heure.items() if ca > 0}
    if len(actifs) < 3:
        return []
    moyenne = sum(actifs.values()) / len(actifs)

    resultats = []
    for heure, ca in sorted(ca_par_heure.items()):
        nb_commandes = len(commandes_par_heure[heure])
        if nb_commandes < MIN_COMMANDES_CRENEAU:
            continue
        if ca >= moyenne * SEUIL_CRENEAU_CREUX:
            continue
        resultats.append({
            "heure": heure,
            "libelle": f"{heure}h – {heure + 1}h",
            "ca": round(ca, 2),
            "commandes": nb_commandes,
            "moyenne_horaire": round(moyenne, 2),
            "ecart_pourcent": round((1 - ca / moyenne) * 100),
            "manque_a_gagner": round(moyenne - ca, 2),
        })
    # Le créneau le plus en retrait d'abord.
    resultats.sort(key=lambda r: r["manque_a_gagner"], reverse=True)
    return resultats[:3]


# --------------------------------------------------------------------------
# 2. Produits en retrait — quoi mettre en avant
# --------------------------------------------------------------------------
def produits_en_retrait(point_de_vente_id, debut, fin):
    """Produits dont la part du chiffre d'affaires est nettement sous la moyenne.

    Règle : un produit vendu au moins dix fois, mais dont la part de CA est
    inférieure à 60 % de la part moyenne d'un produit, est un candidat — soit à
    une mise en avant, soit à un retrait de la carte s'il ne décolle pas.
    """
    detail = kpi.detail_par_produit(point_de_vente_id, debut, fin)
    if len(detail) < 3:
        return []

    ca_total = sum(r["ca"] for r in detail)
    if ca_total <= 0:
        return []
    part_moyenne = 100 / len(detail)

    resultats = []
    for r in detail:
        part = r["ca"] / ca_total * 100
        if r["quantite"] < MIN_VENTES_PRODUIT:
            continue
        if part >= part_moyenne * SEUIL_PRODUIT_RETRAIT:
            continue
        resultats.append({
            "nom": r["nom"],
            "quantite": r["quantite"],
            "ca": round(r["ca"], 2),
            "part": round(part, 1),
            "part_moyenne": round(part_moyenne, 1),
        })
    resultats.sort(key=lambda r: r["part"])
    return resultats[:3]


# --------------------------------------------------------------------------
# 3. Produits associés — quelles formules créer
# --------------------------------------------------------------------------
def associations_produits(point_de_vente_id, debut, fin):
    """Paires de produits fréquemment achetées dans une même commande.

    Règle : on compte, pour chaque paire de produits distincts, le nombre de
    commandes qui contiennent les deux. Les paires les plus fréquentes sont des
    candidates naturelles à une formule. On indique aussi le panier moyen de ces
    commandes, comparé au panier moyen général : une association qui fait monter
    le panier mérite d'être encouragée.
    """
    lignes = (
        db.session.query(
            LigneCommande.commande_id, Produit.nom, LigneCommande.montant
        )
        .join(Commande, LigneCommande.commande_id == Commande.id_commande)
        .join(Produit, LigneCommande.produit_id == Produit.id_produit)
        .filter(Commande.point_de_vente_id == point_de_vente_id)
        .filter(Commande.date_heure >= debut, Commande.date_heure < fin)
        .all()
    )
    if not lignes:
        return []

    produits_par_commande = {}
    montant_par_commande = {}
    for commande_id, nom, montant in lignes:
        produits_par_commande.setdefault(commande_id, set()).add(nom)
        montant_par_commande[commande_id] = (
            montant_par_commande.get(commande_id, 0.0) + float(montant or 0)
        )

    total_commandes = len(produits_par_commande)
    if total_commandes == 0:
        return []
    panier_moyen_global = sum(montant_par_commande.values()) / total_commandes

    # Comptage des paires (produits triés pour que la paire soit stable).
    occurrences = {}
    for commande_id, produits in produits_par_commande.items():
        for paire in combinations(sorted(produits), 2):
            occurrences.setdefault(paire, []).append(commande_id)

    resultats = []
    for paire, ids in occurrences.items():
        if len(ids) < MIN_COMMANDES_PAIRE:
            continue
        panier_paire = sum(montant_par_commande[i] for i in ids) / len(ids)
        resultats.append({
            "produits": list(paire),
            "commandes": len(ids),
            "part_commandes": round(len(ids) / total_commandes * 100, 1),
            "panier_moyen": round(panier_paire, 2),
            "panier_moyen_global": round(panier_moyen_global, 2),
            "ecart_panier": round(panier_paire - panier_moyen_global, 2),
        })
    resultats.sort(key=lambda r: r["commandes"], reverse=True)
    return resultats[:NB_PAIRES]
