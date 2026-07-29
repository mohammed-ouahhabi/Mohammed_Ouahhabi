"""Tests de la recomposition de l'horodatage (date + heure en colonnes séparées).

Beaucoup d'exports de caisse séparent la date et l'heure. Sans recomposition,
toutes les ventes d'une journée porteraient le même horodatage et seraient
regroupées en une seule commande — faussant le nombre de commandes, le panier
moyen et les pics horaires.
"""
import os
import tempfile
from datetime import datetime

from app.models import PointDeVente, Utilisateur, Commande, ROLE_MANAGER
from app.services import pipeline


def _ecrire(contenu):
    fd, chemin = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin


def _contexte():
    pdv = PointDeVente.query.first()
    manager = Utilisateur.query.filter_by(role=ROLE_MANAGER).first()
    return pdv.id_point_de_vente, manager


# --- Détection ------------------------------------------------------------

def test_colonne_heure_detectee_automatiquement(app):
    chemin = _ecrire(
        "date_commande,nom_pizza,quantite,prix_total,heure_commande\n"
        "2026-01-01,Reine,1,13.90,11:38:36\n"
    )
    try:
        info = pipeline.detecter_colonnes(chemin)
        assert info["auto"]["date"] == "date_commande"
        assert info["auto"]["heure"] == "heure_commande"
        assert info["auto"]["produit"] == "nom_pizza"   # alias ajouté
        assert info["auto"]["montant"] == "prix_total"
    finally:
        os.remove(chemin)


# --- Recomposition --------------------------------------------------------

def test_date_et_heure_separees_donnent_horodatages_complets(app, db):
    """Trois ventes le même jour à trois heures distinctes = 3 commandes."""
    pdv_id, manager = _contexte()
    chemin = _ecrire(
        "date_commande,produit,quantite,montant,heure_commande\n"
        "2026-01-05,Reine,1,13.90,11:38:36\n"
        "2026-01-05,Pepperoni,1,14.90,12:15:00\n"
        "2026-01-05,Calzone,1,14.50,19:47\n"        # format HH:MM également accepté
    )
    try:
        avant = Commande.query.count()
        rapport = pipeline.traiter_fichier(chemin, "separe.csv", manager, pdv_id)
        assert rapport["lignes_integrees"] == 3
        assert rapport["lignes_rejetees"] == 0
        # 3 horodatages distincts -> 3 commandes (et non 1 seule pour la journée).
        assert Commande.query.count() == avant + 3

        heures = sorted(
            c.date_heure.strftime("%H:%M:%S")
            for c in Commande.query.filter(
                Commande.date_heure >= datetime(2026, 1, 5),
                Commande.date_heure < datetime(2026, 1, 6),
            ).all()
        )
        assert heures == ["11:38:36", "12:15:00", "19:47:00"]
    finally:
        os.remove(chemin)


def test_date_contenant_deja_l_heure_non_regression(app, db):
    """Cas historique : la date porte l'heure. Le comportement est inchangé,
    et une éventuelle colonne heure est ignorée (pas de double heure)."""
    pdv_id, manager = _contexte()
    chemin = _ecrire(
        "date,produit,quantite,montant,heure\n"
        "2026-02-01 12:15:00,Reine,1,13.90,23:59:59\n"
    )
    try:
        pipeline.traiter_fichier(chemin, "deja_heure.csv", manager, pdv_id)
        commande = (
            Commande.query.filter(
                Commande.date_heure >= datetime(2026, 2, 1),
                Commande.date_heure < datetime(2026, 2, 2),
            ).first()
        )
        # La date fait foi : 12:15:00, et non 23:59:59.
        assert commande.date_heure.strftime("%H:%M:%S") == "12:15:00"
    finally:
        os.remove(chemin)


def test_heure_vide_ou_invalide_conserve_la_date_sans_rejet(app, db):
    """L'heure est une précision, pas une condition de validité."""
    pdv_id, manager = _contexte()
    chemin = _ecrire(
        "date_commande,produit,quantite,montant,heure_commande\n"
        "2026-03-10,Reine,1,13.90,\n"            # heure vide
        "2026-03-11,Pepperoni,1,14.90,pasunheure\n"  # heure invalide
    )
    try:
        rapport = pipeline.traiter_fichier(chemin, "heure_vide.csv", manager, pdv_id)
        assert rapport["lignes_integrees"] == 2
        assert rapport["lignes_rejetees"] == 0   # aucune ligne rejetée
        commande = Commande.query.filter(
            Commande.date_heure >= datetime(2026, 3, 10),
            Commande.date_heure < datetime(2026, 3, 11),
        ).first()
        assert commande.date_heure.strftime("%H:%M:%S") == "00:00:00"
    finally:
        os.remove(chemin)


def test_horodatage_unitaire(app):
    """Règles de recomposition, isolées de tout accès base."""
    # date seule + heure -> recomposition
    assert pipeline._horodatage("2026-01-01", "11:38:36") == datetime(2026, 1, 1, 11, 38, 36)
    # format HH:MM accepté
    assert pipeline._horodatage("2026-01-01", "19:47") == datetime(2026, 1, 1, 19, 47)
    # la date porte déjà l'heure : elle fait foi
    assert pipeline._horodatage("2026-01-01 12:15:00", "23:59:59") == datetime(2026, 1, 1, 12, 15)
    # heure absente / invalide : date seule
    assert pipeline._horodatage("2026-01-01", None) == datetime(2026, 1, 1)
    assert pipeline._horodatage("2026-01-01", "zzz") == datetime(2026, 1, 1)
    # date invalide : rien à recomposer
    assert pipeline._horodatage("32/13/2026", "11:00") is None
