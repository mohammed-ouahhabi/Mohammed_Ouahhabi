"""Amorçage au démarrage (déploiement).

Sur le plan gratuit de Render, il n'y a pas d'accès shell pour lancer des
commandes après le déploiement. Ce script rend l'application immédiatement
utilisable : si la base ne contient aucun utilisateur, il charge le jeu de
démonstration (qui crée notamment le compte manager).

Idempotent : si des utilisateurs existent déjà, il ne fait rien (aucune donnée
n'est écrasée lors des redéploiements).

Appelé dans le startCommand : `python -m scripts.bootstrap`.
"""
from app import create_app
from app.models import Utilisateur


def main():
    app = create_app()
    with app.app_context():
        if Utilisateur.query.count() == 0:
            from scripts.seed import executer_seed
            executer_seed()
            print("Bootstrap : jeu de démonstration chargé.")
        else:
            print("Bootstrap : données déjà présentes, rien à faire.")


if __name__ == "__main__":
    main()
