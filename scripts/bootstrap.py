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
            return
        # Garantit que les comptes de démo du README existent et fonctionnent,
        # même si la base a été amorcée par une version antérieure du seed.
        from app.extensions import db
        from app.models import PointDeVente
        from app.models import ROLE_MANAGER  # adapte l'import si besoin
        pdv = PointDeVente.query.first()
        for nom, email in [("Ahmed O.", "manager@pdv-nanterre.fr"),
                           ("Responsable Nanterre", "responsable@pdv-nanterre.fr")]:
            u = Utilisateur.query.filter_by(email=email).first()
            if u is None:
                u = Utilisateur(nom=nom, email=email, role=ROLE_MANAGER, actif=True,
                                point_de_vente_id=pdv.id_point_de_vente)
                db.session.add(u)
            u.definir_mot_de_passe("motdepasse123")
            u.actif = True
        db.session.commit()
        print("Bootstrap : comptes de démonstration vérifiés.")

if __name__ == "__main__":
    main()
