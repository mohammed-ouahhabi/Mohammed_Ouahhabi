"""Fixtures partagées par les tests (pytest).

On utilise la configuration `testing` : base SQLite en mémoire, CSRF désactivé
(pour pouvoir poster les formulaires sans jeton dans les tests).
"""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import (
    PointDeVente,
    Utilisateur,
    Produit,
    Commande,
    LigneCommande,
    Vente,
    ROLE_MANAGER,
    ROLE_ASSISTANT,
    ROLE_PREMIER_EQUIPIER,
    ROLE_EQUIPIER,
)
from datetime import datetime


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        _semer(_db)
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def _semer(db):
    """Petit jeu de données déterministe pour les tests."""
    pdv = PointDeVente(nom="Nanterre", ville="Nanterre")
    db.session.add(pdv)
    db.session.flush()

    roles = {
        ROLE_MANAGER: "manager@test.fr",
        ROLE_ASSISTANT: "assistant@test.fr",
        ROLE_PREMIER_EQUIPIER: "premier@test.fr",
        ROLE_EQUIPIER: "equipier@test.fr",
    }
    for role, email in roles.items():
        u = Utilisateur(nom=role.capitalize(), email=email, role=role, actif=True,
                        point_de_vente_id=pdv.id_point_de_vente)
        u.definir_mot_de_passe("motdepasse123")
        db.session.add(u)

    reine = Produit(nom="Reine", categorie="Pizza", prix_unitaire=13.90)
    boisson = Produit(nom="Boisson 33cl", categorie="Boisson", prix_unitaire=2.50)
    db.session.add_all([reine, boisson])
    db.session.flush()

    # Deux commandes : CA total = (2*13.90 + 2.50) + 13.90 = 44.20
    c1 = Commande(point_de_vente_id=pdv.id_point_de_vente,
                  date_heure=datetime(2026, 6, 1, 12, 15), montant_total=30.30)
    c1.lignes.append(LigneCommande(produit_id=reine.id_produit, quantite=2, montant=27.80))
    c1.lignes.append(LigneCommande(produit_id=boisson.id_produit, quantite=1, montant=2.50))
    c2 = Commande(point_de_vente_id=pdv.id_point_de_vente,
                  date_heure=datetime(2026, 6, 1, 20, 0), montant_total=13.90)
    c2.lignes.append(LigneCommande(produit_id=reine.id_produit, quantite=1, montant=13.90))
    db.session.add_all([c1, c2])
    db.session.flush()

    # Une vente (encaissement) par commande — cohérente avec montant_total.
    db.session.add(Vente(commande_id=c1.id_commande, montant=30.30,
                         date_vente=c1.date_heure, mode_paiement="Carte"))
    db.session.add(Vente(commande_id=c2.id_commande, montant=13.90,
                         date_vente=c2.date_heure, mode_paiement="Espèces"))
    db.session.commit()


def connexion(client, email, mot_de_passe="motdepasse123"):
    """Helper : authentifie un client de test."""
    return client.post(
        "/login",
        data={"email": email, "mot_de_passe": mot_de_passe},
        follow_redirects=True,
    )
