"""Tests de la couche « aide à la décision » : alertes et prévision.

Tests déterministes : on injecte des données contrôlées et on vérifie les seuils.
"""
from datetime import datetime, timedelta

from app.extensions import db
from app.models import PointDeVente, Produit, Commande, LigneCommande
from app.services import alertes, prevision, kpi


def _ajouter_ventes(pdv_id, produit_id, quand, nombre, prix=10.0):
    """Crée `nombre` commandes (1 ligne chacune) à l'instant `quand`, décalées
    d'une minute pour former des tickets distincts."""
    for i in range(nombre):
        dh = quand + timedelta(minutes=i)
        c = Commande(point_de_vente_id=pdv_id, date_heure=dh, montant_total=prix)
        c.lignes.append(LigneCommande(produit_id=produit_id, quantite=1, montant=prix))
        db.session.add(c)
    db.session.commit()


# --- Alertes ---------------------------------------------------------------

def test_alerte_decrochage_declenchee(app, db):
    pdv = PointDeVente.query.first()
    produit = Produit(nom="ProduitEnChute", categorie="Test", prix_unitaire=10)
    db.session.add(produit)
    db.session.flush()

    maintenant = kpi._maintenant()
    # Période précédente (il y a ~45 jours) : 20 ventes.
    _ajouter_ventes(pdv.id_point_de_vente, produit.id_produit, maintenant - timedelta(days=45), 20)
    # Période courante (il y a ~5 jours) : 4 ventes seulement (−80 %).
    _ajouter_ventes(pdv.id_point_de_vente, produit.id_produit, maintenant - timedelta(days=5), 4)

    liste = alertes.calculer_alertes(pdv.id_point_de_vente, jours=30)
    decrochages = [a for a in liste if a["type"] == "produit_decrochage"
                   and "ProduitEnChute" in a["titre"]]
    assert len(decrochages) == 1
    assert decrochages[0]["niveau"] == "attention"


def test_alerte_decrochage_non_declenchee_sous_seuil(app, db):
    pdv = PointDeVente.query.first()
    produit = Produit(nom="ProduitStable", categorie="Test", prix_unitaire=10)
    db.session.add(produit)
    db.session.flush()

    maintenant = kpi._maintenant()
    # 20 ventes avant, 18 après : −10 %, sous le seuil de 30 %.
    _ajouter_ventes(pdv.id_point_de_vente, produit.id_produit, maintenant - timedelta(days=45), 20)
    _ajouter_ventes(pdv.id_point_de_vente, produit.id_produit, maintenant - timedelta(days=5), 18)

    liste = alertes.calculer_alertes(pdv.id_point_de_vente, jours=30)
    decrochages = [a for a in liste if a["type"] == "produit_decrochage"
                   and "ProduitStable" in a["titre"]]
    assert decrochages == []


def test_aucune_alerte_renvoie_liste(app, db):
    # Sur un PDV sans données, la fonction renvoie une liste (vide), pas d'erreur.
    pdv_vide = PointDeVente(nom="Vide", ville="Nulle-part")
    db.session.add(pdv_vide)
    db.session.commit()
    liste = alertes.calculer_alertes(pdv_vide.id_point_de_vente, jours=30)
    assert liste == []


# --- Prévision -------------------------------------------------------------

def test_prevision_creneau_coherente(app, db):
    pdv = PointDeVente.query.first()
    produit = Produit(nom="ProduitPrev", categorie="Test", prix_unitaire=10)
    db.session.add(produit)
    db.session.flush()

    # Trois jeudis, chacun avec 20 commandes à 19h -> moyenne du créneau = 20.
    jeudis = [datetime(2026, 6, 4, 19, 0), datetime(2026, 6, 11, 19, 0), datetime(2026, 6, 18, 19, 0)]
    assert all(j.weekday() == 3 for j in jeudis)  # 3 = jeudi
    for jeudi in jeudis:
        _ajouter_ventes(pdv.id_point_de_vente, produit.id_produit, jeudi, 20)

    moyennes = prevision.moyenne_par_creneau(pdv.id_point_de_vente)
    assert abs(moyennes[(3, 19)] - 20) < 0.001


def test_prevision_7_jours_structure(app, db):
    pdv = PointDeVente.query.first()
    resultat = prevision.prevoir_7_jours(pdv.id_point_de_vente)
    assert len(resultat["jours"]) == 7
    assert len(resultat["labels"]) == 7
    assert len(resultat["valeurs"]) == 7
    # Toutes les estimations sont des nombres positifs ou nuls.
    assert all(v >= 0 for v in resultat["valeurs"])
