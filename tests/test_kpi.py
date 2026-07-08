"""Tests unitaires du service KPI (calculs des indicateurs)."""
from datetime import datetime

from app.models import PointDeVente
from app.services import kpi


def _pdv_id(db):
    return PointDeVente.query.first().id_point_de_vente


def test_chiffre_affaires(app, db):
    pdv = _pdv_id(db)
    # 27.80 + 2.50 + 13.90 = 44.20
    assert kpi.chiffre_affaires(pdv) == 44.20


def test_nombre_commandes(app, db):
    pdv = _pdv_id(db)
    assert kpi.nombre_commandes(pdv) == 2


def test_produits_vendus(app, db):
    pdv = _pdv_id(db)
    # quantités : 2 + 1 + 1 = 4
    assert kpi.produits_vendus(pdv) == 4


def test_panier_moyen(app, db):
    pdv = _pdv_id(db)
    # 44.20 / 2 = 22.10
    assert round(kpi.panier_moyen(pdv), 2) == 22.10


def test_panier_moyen_sans_commande(app, db):
    # Un PDV inexistant n'a aucune commande : pas de division par zéro.
    assert kpi.panier_moyen(999) == 0.0


def test_top_produits_ordonne(app, db):
    pdv = _pdv_id(db)
    top = kpi.top_produits(pdv)
    assert top[0]["nom"] == "Reine"          # 3 unités
    assert top[0]["quantite"] == 3
    assert top[1]["nom"] == "Boisson 33cl"   # 1 unité


def test_detail_par_produit_parts(app, db):
    pdv = _pdv_id(db)
    detail = kpi.detail_par_produit(pdv)
    # La somme des parts (%) doit avoisiner 100.
    assert 98 <= sum(r["part"] for r in detail) <= 102


def test_pics_activite(app, db):
    pdv = _pdv_id(db)
    pics = kpi.pics_activite(pdv)
    assert pics[12] == 1   # une commande à 12h
    assert pics[20] == 1   # une commande à 20h
    assert pics[3] == 0
