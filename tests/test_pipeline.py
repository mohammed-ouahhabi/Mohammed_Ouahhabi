"""Tests unitaires du pipeline d'import (pandas + contrôles qualité)."""
import io
import os
import tempfile

import pytest

from app.models import Utilisateur, Commande, ROLE_MANAGER
from app.services import pipeline


def _ecrire_csv(contenu):
    fd, chemin = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin


def test_lire_colonnes_manquantes(app):
    chemin = _ecrire_csv("date,produit\n2026-06-01,Reine\n")
    try:
        with pytest.raises(pipeline.ErreurFichier):
            pipeline.lire_et_normaliser(chemin)
    finally:
        os.remove(chemin)


def test_entetes_avec_accents_tolerees(app):
    # « quantité » (accent) doit être reconnu comme « quantite ».
    chemin = _ecrire_csv("date,produit,quantité,montant\n2026-06-01 12:00,Reine,1,13.90\n")
    try:
        df = pipeline.lire_et_normaliser(chemin)
        assert list(df.columns) == pipeline.COLONNES_ATTENDUES
    finally:
        os.remove(chemin)


def test_controle_qualite_detecte_anomalies(app):
    contenu = (
        "date,produit,quantite,montant\n"
        "2026-06-01 12:00,Reine,1,13.90\n"      # valide
        "2026-06-01 12:00,Reine,1,13.90\n"      # doublon
        "01/13/2026,Reine,1,13.90\n"            # date invalide
        "2026-06-02 12:00,,1,13.90\n"           # produit manquant
        "2026-06-02 12:00,Reine,-1,13.90\n"     # quantité invalide
        "2026-06-02 12:00,Reine,1,abc\n"        # montant invalide
    )
    chemin = _ecrire_csv(contenu)
    try:
        df = pipeline.lire_et_normaliser(chemin)
        valides, rapport = pipeline.controler_qualite(df)
        assert rapport["lignes_lues"] == 6
        assert rapport["lignes_valides"] == 1
        assert rapport["lignes_rejetees"] == 5
        assert rapport["anomalies"]["doublons"] == 1
        assert rapport["anomalies"]["format_date"] == 1
        assert rapport["anomalies"]["valeurs_manquantes"] == 1
        assert rapport["anomalies"]["quantite_invalide"] == 1
        assert rapport["anomalies"]["montant_invalide"] == 1
    finally:
        os.remove(chemin)


def test_traitement_complet_integre_en_base(app, db):
    from app.models import PointDeVente
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    contenu = (
        "date,produit,quantite,montant\n"
        "2026-07-01 12:00,Reine,2,27.80\n"
        "2026-07-01 12:00,Boisson 33cl,1,2.50\n"   # même horodatage -> même commande
        "2026-07-01 19:00,Pepperoni,1,14.90\n"
    )
    chemin = _ecrire_csv(contenu)
    try:
        avant = Commande.query.count()
        rapport = pipeline.traiter_fichier(chemin, "test.csv", manager, pdv.id_point_de_vente)
        assert rapport["lignes_integrees"] == 3
        assert rapport["statut"] == "termine"
        # 3 lignes sur 2 horodatages distincts => 2 nouvelles commandes.
        assert Commande.query.count() == avant + 2
    finally:
        os.remove(chemin)


def test_fichier_illisible_leve_erreur(app):
    # Un contenu sans en-têtes attendus déclenche une ErreurFichier claire.
    chemin = _ecrire_csv("colonne_inconnue\nvaleur\n")
    try:
        with pytest.raises(pipeline.ErreurFichier):
            pipeline.lire_et_normaliser(chemin)
    finally:
        os.remove(chemin)
