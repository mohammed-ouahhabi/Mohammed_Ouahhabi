"""Écran « Import de données » — pipeline d'import CSV en 2 étapes (back-office).

Flux :
    1. Upload         -> on lit les en-têtes, on propose une correspondance auto.
    2. Correspondance -> l'utilisateur associe ses colonnes au schéma cible.
    3. Traitement     -> contrôles qualité + intégration + récapitulatif.

Cette étape de correspondance rend l'import compatible avec n'importe quel
magasin, quel que soit le nom de ses colonnes (couche « connecteur »).

Le fichier déposé est conservé EN BASE entre les deux étapes, et non sur le
disque local : sur un hébergement de type conteneur, le système de fichiers est
éphémère (un redéploiement ou une mise en veille l'efface), ce qui
interromprait l'import en cours par un « fichier introuvable ».

Accès réservé au Manager et à l'Assistant manager.
"""
import os
import tempfile
import uuid
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..decorators import role_requis
from ..extensions import db
from ..forms import ImportForm
from ..models import ImportFichier, ImportTemporaire, ROLE_MANAGER, ROLE_ASSISTANT
from ..services import pipeline

bp = Blueprint("imports", __name__, url_prefix="/import")

ACCES_IMPORT = role_requis(ROLE_MANAGER, ROLE_ASSISTANT)

# Durée de conservation d'un dépôt non traité (import abandonné).
DUREE_CONSERVATION = timedelta(hours=1)


def _historique():
    return ImportFichier.query.order_by(ImportFichier.date_import.desc()).limit(10).all()


def _purger_depots_expires():
    """Supprime les dépôts abandonnés depuis plus d'une heure."""
    limite = datetime.utcnow() - DUREE_CONSERVATION
    ImportTemporaire.query.filter(ImportTemporaire.date_depot < limite).delete()
    db.session.commit()


@bp.route("/", methods=["GET", "POST"])
@login_required
@ACCES_IMPORT
def index():
    form = ImportForm()

    # Étape 1 : réception du fichier -> détection des colonnes -> correspondance.
    if form.validate_on_submit():
        fichier = form.fichier.data
        nom_securise = secure_filename(fichier.filename) or "import.csv"
        contenu = fichier.read()

        _purger_depots_expires()

        # Le fichier est conservé en base, seul stockage persistant disponible.
        jeton = uuid.uuid4().hex
        db.session.add(ImportTemporaire(
            jeton=jeton,
            nom_fichier=nom_securise,
            contenu=contenu,
            utilisateur_id=current_user.id_utilisateur,
        ))
        db.session.commit()

        try:
            with _fichier_temporaire(contenu) as chemin:
                info = pipeline.detecter_colonnes(chemin)
        except pipeline.ErreurFichier as exc:
            ImportTemporaire.query.filter_by(jeton=jeton).delete()
            db.session.commit()
            flash(str(exc), "error")
            return redirect(url_for("imports.index"))

        return render_template(
            "imports/correspondance.html",
            info=info,
            jeton=jeton,
            nom_fichier=nom_securise,
            champs=pipeline.CHAMPS_CIBLE,
            champs_optionnels=pipeline.CHAMPS_OPTIONNELS,
            libelles=pipeline.LIBELLES_CHAMPS,
        )

    return render_template(
        "imports/index.html", form=form, rapport=None, historique=_historique()
    )


class _fichier_temporaire:
    """Écrit un contenu binaire dans un fichier temporaire, le temps du traitement.

    pandas travaille à partir d'un chemin ; le fichier est supprimé à la sortie
    du bloc, quoi qu'il arrive.
    """

    def __init__(self, contenu):
        self.contenu = contenu
        self.chemin = None

    def __enter__(self):
        fd, self.chemin = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "wb") as f:
            f.write(self.contenu)
        return self.chemin

    def __exit__(self, *args):
        if self.chemin and os.path.exists(self.chemin):
            os.remove(self.chemin)
        return False


@bp.route("/traiter", methods=["POST"])
@login_required
@ACCES_IMPORT
def traiter():
    """Étape 3 : traitement effectif avec la correspondance choisie."""
    jeton = request.form.get("jeton", "")
    depot = ImportTemporaire.query.filter_by(jeton=jeton).first() if jeton else None

    if depot is None:
        flash(
            "Ce dépôt n'est plus disponible (import abandonné depuis plus d'une "
            "heure, ou déjà traité). Merci de recharger le fichier.",
            "error",
        )
        return redirect(url_for("imports.index"))

    nom_fichier = depot.nom_fichier

    # Correspondance saisie par l'utilisateur : champ_cible -> colonne source
    # (champs obligatoires + champs facultatifs comme le mode de paiement).
    champs = pipeline.CHAMPS_CIBLE + pipeline.CHAMPS_OPTIONNELS
    mapping = {c: (request.form.get("map_" + c) or None) for c in champs}
    forcer = request.form.get("forcer") == "1"

    rapport = None
    try:
        with _fichier_temporaire(depot.contenu) as chemin:
            # Garde-fou : ce fichier a-t-il déjà été importé avec succès ?
            # On bloque par défaut ; l'utilisateur peut forcer en connaissance de cause.
            if not forcer:
                precedent = pipeline.import_precedent(
                    pipeline.calculer_hash_fichier(chemin)
                )
                if precedent is not None:
                    return render_template(
                        "imports/doublon.html",
                        precedent=precedent,
                        jeton=jeton,
                        nom_fichier=nom_fichier,
                        mapping=mapping,
                    )

            rapport = pipeline.traiter_fichier(
                chemin, nom_fichier, current_user,
                current_user.point_de_vente_id, mapping=mapping,
            )

        if rapport["lignes_integrees"] > 0:
            flash(f"Import terminé : {rapport['lignes_integrees']} lignes intégrées.", "success")
        elif rapport["lignes_ignorees"] > 0:
            flash(
                f"Aucune nouvelle donnée : les {rapport['lignes_ignorees']} lignes "
                "étaient déjà présentes dans l'entrepôt. Les indicateurs sont inchangés.",
                "warning",
            )
        else:
            flash("Aucune ligne valide n'a pu être intégrée.", "warning")
    except pipeline.ErreurFichier as exc:
        flash(str(exc), "error")

    # Le dépôt a rempli son office : on le supprime.
    ImportTemporaire.query.filter_by(jeton=jeton).delete()
    db.session.commit()

    return render_template(
        "imports/index.html", form=ImportForm(), rapport=rapport, historique=_historique()
    )
