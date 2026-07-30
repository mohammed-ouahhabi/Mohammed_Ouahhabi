"""Réinitialisation complète de la base de DÉVELOPPEMENT.

Supprime la base locale, rejoue toutes les migrations, puis recharge le jeu de
démonstration. Utile quand la base locale s'est désynchronisée du code — cas
typique après plusieurs récupérations successives de nouvelles versions.

Deux garde-fous, car l'opération est destructrice :
  1. le script REFUSE de s'exécuter sur autre chose qu'une base SQLite locale ;
  2. il demande une confirmation explicite (saisir « oui »).

Utilisation :
    python -m scripts.reinit_db          # avec confirmation
    python -m scripts.reinit_db --oui    # sans confirmation (usage scripté)
"""
import os
import sys

from app import create_app
from app.extensions import db


def _verifier_environnement(app):
    """Interdit l'exécution ailleurs que sur une base SQLite locale."""
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    config = os.environ.get("FLASK_CONFIG", "default")

    if not uri.startswith("sqlite:///"):
        raise SystemExit(
            "REFUS : la base visée n'est pas une base SQLite locale.\n"
            f"        Base : {uri.split('@')[-1]}\n"
            "        Ce script ne réinitialise que l'environnement de développement."
        )
    if config == "production" or os.environ.get("DATABASE_URL"):
        raise SystemExit(
            "REFUS : la configuration ou la variable DATABASE_URL désigne un\n"
            "        environnement de production. Opération annulée."
        )
    return uri.replace("sqlite:///", "")


def main():
    app = create_app()
    with app.app_context():
        chemin = _verifier_environnement(app)

        print("Réinitialisation de la base de développement")
        print(f"  Fichier : {chemin}")
        print("  Toutes les données locales seront perdues.")

        if "--oui" not in sys.argv:
            reponse = input("  Confirmer ? (tapez « oui ») : ").strip().lower()
            if reponse != "oui":
                print("Annulé.")
                return

        # 1. Suppression du fichier de base.
        db.session.remove()
        db.engine.dispose()
        if os.path.isfile(chemin):
            os.remove(chemin)
            print("  [1/3] Ancienne base supprimée.")
        else:
            print("  [1/3] Aucune base existante.")

        # 2. Migrations rejouées depuis l'origine.
        from flask_migrate import upgrade
        upgrade()
        print("  [2/3] Migrations appliquées.")

        # 3. Jeu de démonstration.
        from scripts.seed import executer_seed
        executer_seed()
        print("  [3/3] Jeu de démonstration rechargé.")

        print("\nTerminé. Vérifiez l'état avec : python -m scripts.diagnostic")


if __name__ == "__main__":
    main()
