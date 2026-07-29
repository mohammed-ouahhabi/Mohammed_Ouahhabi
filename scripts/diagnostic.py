"""Diagnostic de l'état de la base locale.

À lancer quand un écran renvoie une erreur alors que les migrations semblent
appliquées. Le script indique quelle base est réellement utilisée, à quelle
révision elle se trouve, et si son schéma correspond à ce que le code attend.

Utilisation :
    python -m scripts.diagnostic
"""
import os

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db

# Colonnes ajoutées par les migrations successives : leur absence signale une
# base restée en arrière.
ATTENDU = {
    "point_de_vente": ["id_point_de_vente", "nom", "ville"],
    "utilisateur": ["id_utilisateur", "email", "role", "mot_de_passe_hash"],
    "commande": ["id_commande", "date_heure", "montant_total"],
    "ligne_commande": ["id_ligne_commande", "quantite", "montant", "cle_idempotence"],
    "vente": ["id_vente", "montant", "mode_paiement", "date_vente"],
    "import_fichier": ["id_import", "lignes_lues", "lignes_rejetees",
                       "lignes_ignorees", "hash_fichier", "statut"],
    "import_temporaire": ["id_import_temporaire", "jeton", "contenu"],
}


def main():
    app = create_app()
    with app.app_context():
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        print("=" * 66)
        print("DIAGNOSTIC DE LA BASE")
        print("=" * 66)
        print(f"Configuration      : {os.environ.get('FLASK_CONFIG', 'default')}")
        print(f"Base utilisée      : {uri}")

        if uri.startswith("sqlite:///"):
            chemin = uri.replace("sqlite:///", "")
            existe = os.path.isfile(chemin)
            print(f"Fichier            : {chemin}")
            print(f"Fichier présent    : {'oui' if existe else 'NON'}")
            if existe:
                print(f"Taille             : {os.path.getsize(chemin) / 1024:.0f} Ko")

        inspecteur = inspect(db.engine)
        tables = set(inspecteur.get_table_names())

        # Révision enregistrée par Flask-Migrate
        try:
            revision = db.session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        except Exception:
            revision = None
        print(f"Révision en base   : {revision or 'AUCUNE (base non gérée par les migrations)'}")

        print("-" * 66)
        problemes = []
        for table, colonnes in ATTENDU.items():
            if table not in tables:
                print(f"  [MANQUE]  table « {table} » absente")
                problemes.append(f"table {table}")
                continue
            presentes = {c["name"] for c in inspecteur.get_columns(table)}
            absentes = [c for c in colonnes if c not in presentes]
            if absentes:
                print(f"  [MANQUE]  {table} : colonne(s) {', '.join(absentes)}")
                problemes.extend(f"{table}.{c}" for c in absentes)
            else:
                print(f"  [OK]      {table}")

        print("=" * 66)
        if problemes:
            print("VERDICT : la base n'est PAS à jour.")
            print()
            print("Corrigez en exécutant, dans le dossier du projet :")
            print('    $env:FLASK_APP = "wsgi.py"')
            print("    flask db upgrade")
            print()
            print("Si la commande répond « already at head » alors que des éléments")
            print("manquent ci-dessus, la base a été créée hors migrations. Repartez")
            print("d'une base neuve :")
            print("    Remove-Item instance\\pilotage.db")
            print("    flask db upgrade")
            print("    python -m scripts.seed")
        else:
            print("VERDICT : la base est à jour. Le schéma correspond au code.")
        print("=" * 66)


if __name__ == "__main__":
    main()
