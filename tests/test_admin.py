"""Tests d'intégration du back-office : CRUD utilisateurs et gestion de compte."""
from tests.conftest import connexion
from app.models import Utilisateur


def test_creation_utilisateur(client, db):
    connexion(client, "manager@test.fr")
    r = client.post(
        "/administration/utilisateurs/nouveau",
        data={
            "nom": "Nouveau Test",
            "email": "nouveau@test.fr",
            "role": "equipier",
            "actif": "y",
            "mot_de_passe": "motdepasse123",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert Utilisateur.query.filter_by(email="nouveau@test.fr").first() is not None


def test_creation_refuse_email_duplique(client, db):
    connexion(client, "manager@test.fr")
    r = client.post(
        "/administration/utilisateurs/nouveau",
        data={"nom": "X", "email": "assistant@test.fr", "role": "equipier",
              "actif": "y", "mot_de_passe": "motdepasse123"},
        follow_redirects=True,
    )
    assert "déjà" in r.get_data(as_text=True).lower()


def test_suppression_utilisateur(client, db):
    connexion(client, "manager@test.fr")
    cible = Utilisateur.query.filter_by(email="equipier@test.fr").first()
    r = client.post(
        f"/administration/utilisateurs/{cible.id_utilisateur}/supprimer",
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert Utilisateur.query.filter_by(email="equipier@test.fr").first() is None


def test_modification_de_son_compte(client, db):
    connexion(client, "equipier@test.fr")
    r = client.post(
        "/mon-compte",
        data={"nom": "Équipier Modifié", "email": "equipier@test.fr"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    u = Utilisateur.query.filter_by(email="equipier@test.fr").first()
    assert u.nom == "Équipier Modifié"


def test_suppression_de_son_compte_rgpd(client, db):
    connexion(client, "premier@test.fr")
    r = client.post("/mon-compte/supprimer", follow_redirects=True)
    assert r.status_code == 200
    assert Utilisateur.query.filter_by(email="premier@test.fr").first() is None
