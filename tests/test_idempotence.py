"""Tests d'idempotence des imports (Lot 1).

Enjeu : réimporter un fichier ne doit JAMAIS gonfler les indicateurs. C'est la
différence entre un pipeline de démonstration et un pipeline fiable.
"""
import os
import tempfile

from app.models import PointDeVente, Utilisateur, ImportFichier, ROLE_MANAGER
from app.services import kpi, pipeline


CONTENU = (
    "date,produit,quantite,montant\n"
    "2026-08-01 12:00,Reine,2,27.80\n"
    "2026-08-01 19:00,Pepperoni,1,14.90\n"
    "2026-08-02 12:30,Calzone,1,14.50\n"
)


def _ecrire(contenu):
    fd, chemin = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin


def _contexte():
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    return pdv.id_point_de_vente, manager


def test_reimport_identique_nintegre_rien_et_ca_inchange(app, db):
    pdv_id, manager = _contexte()
    chemin = _ecrire(CONTENU)
    try:
        premier = pipeline.traiter_fichier(chemin, "ventes.csv", manager, pdv_id)
        assert premier["lignes_integrees"] == 3
        assert premier["lignes_ignorees"] == 0
        ca_apres_premier = kpi.chiffre_affaires(pdv_id)

        # Réimport du MÊME fichier : rien de nouveau, CA strictement identique.
        second = pipeline.traiter_fichier(chemin, "ventes.csv", manager, pdv_id)
        assert second["lignes_lues"] == 3
        assert second["lignes_integrees"] == 0
        assert second["lignes_ignorees"] == 3
        assert kpi.chiffre_affaires(pdv_id) == ca_apres_premier
    finally:
        os.remove(chemin)


def test_recouvrement_partiel_nintegre_que_les_nouvelles(app, db):
    pdv_id, manager = _contexte()
    chemin1 = _ecrire(CONTENU)
    # Le second fichier reprend les 3 lignes précédentes et en ajoute 2.
    chemin2 = _ecrire(
        CONTENU
        + "2026-08-03 12:00,Margherita,1,11.90\n"
        + "2026-08-03 19:30,4 Fromages,2,31.80\n"
    )
    try:
        pipeline.traiter_fichier(chemin1, "j1.csv", manager, pdv_id)
        ca_avant = kpi.chiffre_affaires(pdv_id)

        rapport = pipeline.traiter_fichier(chemin2, "j1_et_j2.csv", manager, pdv_id)
        assert rapport["lignes_lues"] == 5
        assert rapport["lignes_integrees"] == 2   # seules les nouvelles
        assert rapport["lignes_ignorees"] == 3    # les lignes déjà connues
        # Le CA n'augmente que du montant des deux lignes nouvelles.
        assert round(kpi.chiffre_affaires(pdv_id) - ca_avant, 2) == 43.70
    finally:
        os.remove(chemin1)
        os.remove(chemin2)


def test_hash_fichier_enregistre_et_detecte(app, db):
    pdv_id, manager = _contexte()
    chemin = _ecrire(CONTENU)
    try:
        empreinte = pipeline.calculer_hash_fichier(chemin)
        assert len(empreinte) == 64  # SHA-256 en hexadécimal

        assert pipeline.import_precedent(empreinte) is None
        pipeline.traiter_fichier(chemin, "ventes.csv", manager, pdv_id)

        # L'empreinte est journalisée et un réimport est détecté.
        journal = ImportFichier.query.order_by(ImportFichier.id_import.desc()).first()
        assert journal.hash_fichier == empreinte
        precedent = pipeline.import_precedent(empreinte)
        assert precedent is not None
        assert precedent.nom_fichier == "ventes.csv"
    finally:
        os.remove(chemin)


def test_cle_ligne_deterministe(app):
    from datetime import datetime
    d = datetime(2026, 8, 1, 12, 0)
    a = pipeline.cle_ligne(d, "Reine", 2, 27.80)
    b = pipeline.cle_ligne(d, "reine", 2, 27.8)   # casse et format différents
    c = pipeline.cle_ligne(d, "Pepperoni", 2, 27.80)
    assert a == b       # même donnée métier -> même clé
    assert a != c       # produit différent -> clé différente


def test_journal_compte_les_lignes_ignorees(app, db):
    pdv_id, manager = _contexte()
    chemin = _ecrire(CONTENU)
    try:
        pipeline.traiter_fichier(chemin, "ventes.csv", manager, pdv_id)
        pipeline.traiter_fichier(chemin, "ventes.csv", manager, pdv_id)
        dernier = ImportFichier.query.order_by(ImportFichier.id_import.desc()).first()
        assert dernier.lignes_lues == 3
        assert dernier.lignes_ignorees == 3
        assert dernier.lignes_integrees == 0   # propriété calculée
        assert dernier.statut == "termine"     # neutralisé, pas en échec
    finally:
        os.remove(chemin)


def test_ecran_doublon_bloque_par_defaut(client, db):
    """L'interface avertit et bloque avant de réintégrer un fichier connu."""
    import io
    from tests.conftest import connexion

    connexion(client, "manager@test.fr")

    def televerser():
        data = {"fichier": (io.BytesIO(CONTENU.encode("utf-8")), "ventes.csv")}
        r = client.post("/import/", data=data, content_type="multipart/form-data")
        import re
        return re.search(r'name="jeton" value="([^"]+)"', r.get_data(as_text=True)).group(1)

    champs = {
        "map_date": "date", "map_produit": "produit",
        "map_quantite": "quantite", "map_montant": "montant",
    }

    # 1er import : traité normalement.
    jeton = televerser()
    r1 = client.post("/import/traiter", data={"jeton": jeton, "nom_fichier": "ventes.csv", **champs})
    assert "Récapitulatif" in r1.get_data(as_text=True)

    # 2e import du même contenu : écran d'avertissement, pas de traitement.
    jeton2 = televerser()
    r2 = client.post("/import/traiter", data={"jeton": jeton2, "nom_fichier": "ventes.csv", **champs})
    html = r2.get_data(as_text=True)
    assert "déjà été importé" in html
    assert "Continuer quand même" in html


def test_reinitialisation_demo_reservee_au_manager(client, db):
    """L'assistant manager (back-office) ne doit PAS pouvoir réinitialiser."""
    from tests.conftest import connexion

    connexion(client, "assistant@test.fr")
    r = client.post("/administration/reinitialiser-demo")
    assert r.status_code == 403
