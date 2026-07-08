"""Application factory.

`create_app()` construit et configure l'application Flask. Ce patron permet
d'instancier plusieurs applications (une pour le serveur, une autre pour les
tests) sans variable globale, et d'éviter les imports circulaires.
"""
import os

from flask import Flask, render_template

from .config import config
from .extensions import db, migrate, login_manager, csrf


def create_app(nom_config=None):
    app = Flask(__name__)

    # Choix de la configuration (variable d'env FLASK_CONFIG, sinon "default").
    nom_config = nom_config or os.environ.get("FLASK_CONFIG", "default")
    app.config.from_object(config.get(nom_config, config["default"]))

    # S'assure que le dossier instance/ existe (base SQLite en dev).
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialisation des extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Les modèles doivent être importés pour être connus de SQLAlchemy/Migrate.
    from . import models  # noqa: F401

    # Enregistrement des blueprints (un par écran / domaine).
    from .blueprints import auth, dashboard, ventes, admin, imports, legal

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(ventes.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(imports.bp)
    app.register_blueprint(legal.bp)

    _enregistrer_gestionnaires_erreurs(app)
    _enregistrer_contexte_templates(app)
    _enregistrer_commandes_cli(app)

    return app


def _enregistrer_gestionnaires_erreurs(app):
    @app.errorhandler(403)
    def acces_interdit(_):
        return render_template("erreurs/403.html"), 403

    @app.errorhandler(404)
    def page_introuvable(_):
        return render_template("erreurs/404.html"), 404

    @app.errorhandler(413)
    def fichier_trop_gros(_):
        return render_template("erreurs/413.html"), 413


def _enregistrer_contexte_templates(app):
    """Rend certaines constantes/utilitaires disponibles dans tous les templates."""
    from .models import ROLE_LABELS

    @app.context_processor
    def injecter():
        return {"ROLE_LABELS": ROLE_LABELS, "nom_app": "Pilotage PDV"}

    # Filtres d'affichage francophones (formatage des nombres et montants).
    @app.template_filter("euros")
    def euros(valeur):
        try:
            return f"{float(valeur):,.2f} €".replace(",", " ").replace(".", ",")
        except (TypeError, ValueError):
            return "0,00 €"

    @app.template_filter("nombre")
    def nombre(valeur):
        try:
            return f"{int(valeur):,}".replace(",", " ")
        except (TypeError, ValueError):
            return "0"


def _enregistrer_commandes_cli(app):
    """Commandes `flask ...` personnalisées (création de l'admin, seed)."""
    import click
    from .extensions import db
    from .models import Utilisateur, PointDeVente, ROLE_MANAGER

    @app.cli.command("creer-admin")
    @click.option("--email", prompt=True)
    @click.option("--nom", prompt=True, default="Administrateur")
    @click.option("--mot-de-passe", prompt=True, hide_input=True, confirmation_prompt=True)
    def creer_admin(email, nom, mot_de_passe):
        """Crée un compte Manager (accès total)."""
        email = email.lower().strip()
        if Utilisateur.query.filter_by(email=email).first():
            click.echo("Un utilisateur avec cet e-mail existe déjà.")
            return
        pdv = PointDeVente.query.first()
        if pdv is None:
            pdv = PointDeVente(nom="Nanterre", ville="Nanterre")
            db.session.add(pdv)
            db.session.flush()
        u = Utilisateur(nom=nom, email=email, role=ROLE_MANAGER, actif=True,
                        point_de_vente_id=pdv.id_point_de_vente)
        u.definir_mot_de_passe(mot_de_passe)
        db.session.add(u)
        db.session.commit()
        click.echo(f"Compte Manager créé : {email}")

    @app.cli.command("seed")
    def seed():
        """Charge un jeu de données de démonstration représentatif."""
        from scripts.seed import executer_seed
        executer_seed()
        click.echo("Données de démonstration chargées.")
