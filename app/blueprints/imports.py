"""Écran « Import de données » — pipeline d'import CSV (back-office).

Accès réservé au Manager et à l'Assistant manager.
"""
import os
import uuid

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..decorators import role_requis
from ..forms import ImportForm
from ..models import ImportFichier, ROLE_MANAGER, ROLE_ASSISTANT
from ..services import pipeline

bp = Blueprint("imports", __name__, url_prefix="/import")

ACCES_IMPORT = role_requis(ROLE_MANAGER, ROLE_ASSISTANT)


@bp.route("/", methods=["GET", "POST"])
@login_required
@ACCES_IMPORT
def index():
    form = ImportForm()
    rapport = None

    if form.validate_on_submit():
        fichier = form.fichier.data
        nom_securise = secure_filename(fichier.filename) or "import.csv"

        # On enregistre le fichier dans un dossier temporaire avant traitement.
        dossier = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(dossier, exist_ok=True)
        chemin = os.path.join(dossier, f"{uuid.uuid4().hex}_{nom_securise}")
        fichier.save(chemin)

        try:
            rapport = pipeline.traiter_fichier(
                chemin,
                nom_securise,
                current_user,
                current_user.point_de_vente_id,
            )
            if rapport["lignes_integrees"] > 0:
                flash(
                    f"Import terminé : {rapport['lignes_integrees']} lignes intégrées.",
                    "success",
                )
            else:
                flash("Aucune ligne valide n'a pu être intégrée.", "warning")
        except pipeline.ErreurFichier as exc:
            # Fichier structurellement invalide : message clair, pas de crash.
            flash(str(exc), "error")
        finally:
            # Nettoyage du fichier temporaire.
            if os.path.exists(chemin):
                os.remove(chemin)

    historique = (
        ImportFichier.query.order_by(ImportFichier.date_import.desc()).limit(10).all()
    )
    return render_template(
        "imports/index.html", form=form, rapport=rapport, historique=historique
    )
