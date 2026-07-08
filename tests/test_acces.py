"""Tests d'intégration : authentification et matrice de contrôle d'accès.

On vérifie que chaque rôle voit exactement les pages auxquelles il a droit.
"""
import pytest

from tests.conftest import connexion


def test_page_login_accessible(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Connexion" in r.get_data(as_text=True)


def test_dashboard_exige_connexion(client):
    # Non connecté : redirection vers /login.
    r = client.get("/tableau-de-bord")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_connexion_reussie_manager(client):
    r = connexion(client, "manager@test.fr")
    assert r.status_code == 200
    assert "Tableau de bord" in r.get_data(as_text=True)


def test_connexion_mauvais_mot_de_passe(client):
    r = connexion(client, "manager@test.fr", "mauvais")
    assert "incorrect" in r.get_data(as_text=True).lower()


# --- Matrice d'accès -------------------------------------------------------
# (email, peut_ventes, peut_admin, peut_import)
CAS = [
    ("manager@test.fr", True, True, True),
    ("assistant@test.fr", True, True, True),
    ("premier@test.fr", True, False, False),
    ("equipier@test.fr", False, False, False),
]


def _statut(client, url):
    return client.get(url).status_code


@pytest.mark.parametrize("email,ventes,admin,imports", CAS)
def test_acces_par_role(client, email, ventes, admin, imports):
    connexion(client, email)

    # Tableau de bord : accessible à tous les rôles connectés.
    assert _statut(client, "/tableau-de-bord") == 200

    # Analyse des ventes.
    assert _statut(client, "/ventes") == (200 if ventes else 403)

    # Back-office administration.
    assert _statut(client, "/administration/") == (200 if admin else 403)

    # Import de données.
    assert _statut(client, "/import/") == (200 if imports else 403)


def test_equipier_ne_voit_pas_lien_admin(client):
    connexion(client, "equipier@test.fr")
    html = client.get("/tableau-de-bord").get_data(as_text=True)
    # Les liens back-office ne doivent pas apparaître dans la barre latérale.
    assert "Import de données" not in html
    assert "Utilisateurs" not in html


def test_manager_voit_liens_admin(client):
    connexion(client, "manager@test.fr")
    html = client.get("/tableau-de-bord").get_data(as_text=True)
    assert "Import de données" in html
    assert "Utilisateurs" in html
