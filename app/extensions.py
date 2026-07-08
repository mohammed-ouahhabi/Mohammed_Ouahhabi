"""Instances des extensions Flask.

On les crée ici, sans les lier à une application, puis on les initialise dans
l'application factory (app/__init__.py) avec init_app(). Ce découpage évite les
imports circulaires et permet de créer plusieurs applications (ex. tests).
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()            # ORM : modèles et accès base
migrate = Migrate()         # migrations de schéma (Flask-Migrate)
login_manager = LoginManager()  # sessions et authentification
csrf = CSRFProtect()        # protection CSRF sur tous les formulaires POST

# Page vers laquelle rediriger un visiteur non connecté.
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"
