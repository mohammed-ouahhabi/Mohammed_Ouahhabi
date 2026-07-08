"""Écran « Import de données » — pipeline d'import CSV en 2 étapes (back-office).

Flux :
    1. Upload         -> on lit les en-têtes, on propose une correspondance auto.
    2. Correspondance -> l'utilisateur associe ses colonnes au schéma cible.
    3. Traitement     -> contrôles qualité + intégration + récapitulatif.

Cette étape de correspondance rend l'import compatible avec n'importe quel
magasin, quel que soit le nom de ses colonnes (couche « connecteur »).

Accès réservé au Manager et à l'Assistant manager.
"""
import os
import time
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


def _historique():
    return ImportFichier.query.order_by(ImportFichier.date_import.desc()).limit(10).all()


def _nettoyer_anciens(dossier, max_age=3600):
    """Supprime les fichiers temporaires de plus d'une heure (abandons d'import)."""
    maintenant = time.time()
    for nom in os.listdir(dossier):
        if nom == ".gitkeep":
            continue
        chemin = os.path.join(dossier, nom)
        try:
            if os.path.isfile(chemin) and maintenant - os.path.getmtime(chemin) > max_age:
                os.remove(chemin)
        except OSError:
            pass


@bp.route("/", methods=["GET", "POST"])
@login_required
@ACCES_IMPORT
def index():
    form = ImportForm()

    # Étape 1 : réception du fichier -> détection des colonnes -> correspondance.
    if form.validate_on_submit():
        fichier = form.fichier.data
        nom_securise = secure_filename(fichier.filename) or "import.csv"

        dossier = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(dossier, exist_ok=True)
        _nettoyer_anciens(dossier)

        # On conserve le fichier entre les 2 étapes via un jeton (nom unique).
        jeton = f"{uuid.uuid4().hex}_{nom_securise}"
        chemin = os.path.join(dossier, jeton)
        fichier.save(chemin)

        try:
            info = pipeline.detecter_colonnes(chemin)
        except pipeline.ErreurFichier as exc:
            os.remove(chemin)
            flash(str(exc), "error")
            return redirect(url_for("imports.index"))

        return render_template(
            "imports/correspondance.html",
            info=info,
            jeton=jeton,
            nom_fichier=nom_securise,
            champs=pipeline.CHAMPS_CIBLE,
            libelles=pipeline.LIBELLES_CHAMPS,
        )

    return render_template(
        "imports/index.html", form=form, rapport=None, historique=_historique()
    )


@bp.route("/traiter", methods=["POST"])
@login_required
@ACCES_IMPORT
def traiter():
    """Étape 3 : traitement effectif avec la correspondance choisie."""
    jeton = secure_filename(request.form.get("jeton", ""))
    nom_fichier = request.form.get("nom_fichier", "import.csv")
    dossier = current_app.config["UPLOAD_FOLDER"]
    chemin = os.path.join(dossier, jeton)

    if not jeton or not os.path.isfile(chemin):
        flash("Fichier expiré ou introuvable. Merci de le recharger.", "error")
        return redirect(url_for("imports.index"))

    # Correspondance saisie par l'utilisateur : champ_cible -> colonne source.
    mapping = {c: (request.form.get("map_" + c) or None) for c in pipeline.CHAMPS_CIBLE}

    rapport = None
    try:
        rapport = pipeline.traiter_fichier(
            chemin, nom_fichier, current_user, current_user.point_de_vente_id, mapping=mapping
        )
        if rapport["lignes_integrees"] > 0:
            flash(f"Import terminé : {rapport['lignes_integrees']} lignes intégrées.", "success")
        else:
            flash("Aucune ligne valide n'a pu être intégrée.", "warning")
    except pipeline.ErreurFichier as exc:
        flash(str(exc), "error")
    finally:
        if os.path.isfile(chemin):
            os.remove(chemin)

    return render_template(
        "imports/index.html", form=ImportForm(), rapport=rapport, historique=_historique()
    )
