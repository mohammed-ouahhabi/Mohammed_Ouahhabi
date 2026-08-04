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


# --- Couche de correspondance (mapping) : import multi-magasins ------------

def test_detection_alias_noms_differents(app):
    # Des colonnes nommées autrement doivent être reconnues automatiquement.
    chemin = _ecrire_csv("date_commande,article,qte,prix\n2026-06-01 12:00,Reine,1,13.90\n")
    try:
        info = pipeline.detecter_colonnes(chemin)
        assert info["auto"]["date"] == "date_commande"
        assert info["auto"]["produit"] == "article"
        assert info["auto"]["quantite"] == "qte"
        assert info["auto"]["montant"] == "prix"
        assert len(info["apercu"]) == 1
    finally:
        os.remove(chemin)


def test_mapping_explicite_colonnes_exotiques(app, db):
    # Colonnes non reconnues automatiquement : l'utilisateur les associe à la main.
    from app.models import PointDeVente
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    chemin = _ecrire_csv("quand,quoi,combien,euros\n2026-07-05 12:00,Reine,2,27.80\n")
    mapping = {"date": "quand", "produit": "quoi", "quantite": "combien", "montant": "euros"}
    try:
        rapport = pipeline.traiter_fichier(chemin, "custom.csv", manager, pdv.id_point_de_vente, mapping=mapping)
        assert rapport["lignes_integrees"] == 1
        assert rapport["statut"] == "termine"
    finally:
        os.remove(chemin)


def test_mapping_incomplet_leve_erreur(app):
    chemin = _ecrire_csv("a,b\n1,2\n")
    try:
        with pytest.raises(pipeline.ErreurFichier):
            pipeline.lire_avec_mapping(
                chemin, {"date": "a", "produit": "b", "quantite": None, "montant": None}
            )
    finally:
        os.remove(chemin)


def test_upload_affiche_ecran_correspondance(client):
    from tests.conftest import connexion
    connexion(client, "manager@test.fr")
    data = {
        "fichier": (
            io.BytesIO(b"date_commande,article,qte,prix\n2026-06-01 12:00,Reine,1,13.90\n"),
            "ventes.csv",
        )
    }
    r = client.post("/import/", data=data, content_type="multipart/form-data", follow_redirects=True)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Correspondance" in html
    assert "date_commande" in html  # la colonne réelle du fichier est proposée


# --------------------------------------------------------------------------
# Normalisation des valeurs de mode de paiement
#
# Le dictionnaire d'alias rapproche les *noms de colonnes* ; la normalisation
# ci-dessous rapproche les *valeurs*. Sans elle, « CB » et « Carte » comptent
# pour deux moyens de paiement distincts dans l'analyse.
# --------------------------------------------------------------------------
def test_les_variantes_de_carte_bancaire_sont_ramenees_a_un_seul_libelle():
    for variante in ["CB", "cb", "Carte", "carte bancaire", "CARTE-BLEUE", "TPE"]:
        assert pipeline.normaliser_mode_paiement(variante) == "Carte"


def test_les_autres_moyens_de_paiement_sont_normalises_aussi():
    assert pipeline.normaliser_mode_paiement("especes") == "Espèces"
    assert pipeline.normaliser_mode_paiement("Espèces") == "Espèces"
    assert pipeline.normaliser_mode_paiement("ticket restaurant") == "Ticket resto"
    assert pipeline.normaliser_mode_paiement("TR") == "Ticket resto"


def test_une_valeur_inconnue_est_conservee_plutot_que_perdue():
    assert pipeline.normaliser_mode_paiement("Crypto") == "Crypto"
    assert pipeline.normaliser_mode_paiement("   ") is None
    assert pipeline.normaliser_mode_paiement(None) is None


def test_un_produit_decouvert_a_l_import_a_un_prix_et_une_categorie(app, db):
    """Un produit absent du catalogue est créé, mais jamais à 0,00 € sans mention.

    Le prix est déduit de la ligne qui l'a fait apparaître, et la catégorie
    indique explicitement qu'un arbitrage reste à faire.
    """
    from app.models import Produit, Utilisateur, PointDeVente

    chemin = _ecrire_csv(
        "date,produit,quantite,montant\n"
        "2026-06-01 12:00,Salade Grecque,2,17.00\n"
    )
    utilisateur = Utilisateur.query.first()
    pdv = PointDeVente.query.first()
    pipeline.traiter_fichier(chemin, "decouverte.csv", utilisateur,
                             pdv.id_point_de_vente)

    produit = Produit.query.filter_by(nom="Salade Grecque").first()
    assert produit is not None
    assert produit.categorie == pipeline.CATEGORIE_A_QUALIFIER
    assert float(produit.prix_unitaire) == 8.50, "17,00 € pour 2 unités"


def test_detecter_colonnes_expose_bien_la_cle_colonnes(app):
    """Le gabarit de correspondance lit `info.colonnes`.

    Un renommage de cette clé ne casse aucun import en apparence : c'est l'écran
    de correspondance qui devient vide, à l'étape 2. Ce test verrouille le
    contrat entre le service et le gabarit.
    """
    chemin = _ecrire_csv(
        "horodatage;libelle_article;nb;total_ttc\n"
        "2026-06-01 12:00;Reine;1;13.90\n"
    )
    info = pipeline.detecter_colonnes(chemin)
    assert info["colonnes"] == ["horodatage", "libelle_article", "nb", "total_ttc"]
    assert set(info) == {"colonnes", "auto", "apercu"}
