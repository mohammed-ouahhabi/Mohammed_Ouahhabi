"""Configuration de l'application.

On définit une classe de base et deux variantes (développement / production).
Le choix se fait par la variable d'environnement FLASK_CONFIG.

Point important pour la soutenance : le code applicatif ne connaît jamais le
moteur de base utilisé. On passe de SQLite (dev) à PostgreSQL (prod) uniquement
en changeant la variable DATABASE_URL — SQLAlchemy rend la bascule transparente.
"""
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class Config:
    """Configuration commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-a-changer")

    # Désactive le suivi des modifications (coûteux et inutile ici).
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sécurité des cookies de session (Flask-Login).
    SESSION_COOKIE_HTTPONLY = True   # cookie inaccessible au JavaScript
    SESSION_COOKIE_SAMESITE = "Lax"  # limite l'envoi du cookie en cross-site

    # Pipeline d'import : taille maximale du fichier accepté (10 Mo, cf. maquette).
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")

    @staticmethod
    def _normalize_db_url(url):
        # Render/Heroku fournissent parfois "postgres://" ; SQLAlchemy attend
        # "postgresql://". On corrige pour éviter une erreur au démarrage.
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


class DevelopmentConfig(Config):
    """Développement local : SQLite, débogage activé."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config._normalize_db_url(
        os.environ.get("DATABASE_URL")
    ) or "sqlite:///" + os.path.join(BASE_DIR, "instance", "pilotage.db")


class ProductionConfig(Config):
    """Production (Render) : PostgreSQL, cookies sécurisés."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True  # cookie envoyé uniquement en HTTPS
    SQLALCHEMY_DATABASE_URI = Config._normalize_db_url(
        os.environ.get("DATABASE_URL")
    ) or "sqlite:///" + os.path.join(BASE_DIR, "instance", "pilotage.db")


class TestingConfig(Config):
    """Tests automatisés : base SQLite en mémoire, CSRF désactivé."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
