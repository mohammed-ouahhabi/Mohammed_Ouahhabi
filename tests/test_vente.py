"""Tests de la table `vente` (encaissements, issue du système source Pulse).

On vérifie l'invariant : chaque commande a une vente, et la somme des montants
encaissés reste cohérente avec la somme des montants de commande.
"""
import io
import os
import tempfile

from sqlalchemy import func

from app.extensions import db
from app.models import Commande, Vente, Utilisateur, PointDeVente, ROLE_MANAGER
from app.services import kpi, pipeline


def test_chaque_commande_a_une_vente(app, db):
    # Dans le jeu de test, une vente par commande.
    assert Vente.query.count() == Commande.query.count()


def test_coherence_montants_ventes_commandes(app, db):
    total_commandes = db.session.query(func.coalesce(func.sum(Commande.montant_total), 0)).scalar()
    total_ventes = db.session.query(func.coalesce(func.sum(Vente.montant), 0)).scalar()
    assert round(float(total_commandes), 2) == round(float(total_ventes), 2)


def test_repartition_paiements(app, db):
    pdv = PointDeVente.query.first()
    rep = kpi.repartition_paiements(pdv.id_point_de_vente)
    modes = {r["mode"]: r["montant"] for r in rep}
    assert modes.get("Carte") == 30.30
    assert modes.get("Espèces") == 13.90


def test_ca_reste_calcule_depuis_lignes(app, db):
    # Le CA ne doit PAS venir de `vente` : c'est toujours la somme des lignes.
    pdv = PointDeVente.query.first()
    assert kpi.chiffre_affaires(pdv.id_point_de_vente) == 44.20


def _ecrire_csv(contenu):
    fd, chemin = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin


def test_import_cree_ventes_avec_mode_paiement(app, db):
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    # Colonne « paiement » reconnue automatiquement (champ facultatif).
    contenu = (
        "date,produit,quantite,montant,paiement\n"
        "2026-08-01 12:00,Reine,1,13.90,Carte\n"
        "2026-08-01 19:00,Pepperoni,1,14.90,Espèces\n"
    )
    chemin = _ecrire_csv(contenu)
    try:
        avant = Vente.query.count()
        rapport = pipeline.traiter_fichier(chemin, "avec_paiement.csv", manager, pdv.id_point_de_vente)
        assert rapport["lignes_integrees"] == 2
        assert Vente.query.count() == avant + 2
        # Les modes de paiement du fichier ont bien été enregistrés.
        modes = {v.mode_paiement for v in Vente.query.all()}
        assert "Carte" in modes and "Espèces" in modes
    finally:
        os.remove(chemin)


def test_import_sans_mode_paiement_reste_valide(app, db):
    # Un fichier sans colonne paiement s'importe sans erreur (mode_paiement NULL).
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    contenu = "date,produit,quantite,montant\n2026-08-02 12:00,Reine,1,13.90\n"
    chemin = _ecrire_csv(contenu)
    try:
        rapport = pipeline.traiter_fichier(chemin, "sans_paiement.csv", manager, pdv.id_point_de_vente)
        assert rapport["lignes_integrees"] == 1
        derniere = Vente.query.order_by(Vente.id_vente.desc()).first()
        assert derniere.mode_paiement is None
    finally:
        os.remove(chemin)
