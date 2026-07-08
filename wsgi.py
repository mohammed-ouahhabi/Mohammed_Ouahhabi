"""Point d'entrée WSGI.

- En développement : `flask run` (via FLASK_APP=wsgi.py) ou `python wsgi.py`.
- En production : `gunicorn wsgi:app` (cf. Procfile / render.yaml).
"""
import os

from app import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "default"))

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
