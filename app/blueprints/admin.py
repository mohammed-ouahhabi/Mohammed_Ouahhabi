"""Back-office — administration des utilisateurs et des sources de données.

Accès réservé au Manager et à l'Assistant manager (décorateur de rôle).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..decorators import role_requis
from ..forms import UtilisateurForm, ConfirmationForm
from ..models import (
    Utilisateur,
    ImportFichier,
    ROLE_MANAGER,
    ROLE_ASSISTANT,
    ROLE_LABELS,
)
from flask_login import logout_user

bp = Blueprint("admin", __name__, url_prefix="/administration")

# Un seul décorateur pour tout le back-office.
ACCES_ADMIN = role_requis(ROLE_MANAGER, ROLE_ASSISTANT)


@bp.route("/")
@login_required
@ACCES_ADMIN
def index():
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom).all()

    # Sources de données : on s'appuie sur l'historique des imports pour dater
    # la dernière mise à jour de chaque « source ».
    dernier_import = (
        ImportFichier.query.order_by(ImportFichier.date_import.desc()).first()
    )
    sources = [
        {"nom": "Ventes", "type": "CSV", "dernier_import": dernier_import},
        {"nom": "Commandes", "type": "CSV", "dernier_import": dernier_import},
        {"nom": "Produits", "type": "CSV", "dernier_import": dernier_import},
    ]

    return render_template(
        "admin/index.html",
        utilisateurs=utilisateurs,
        sources=sources,
        role_labels=ROLE_LABELS,
        suppression_form=ConfirmationForm(),
    )


@bp.route("/utilisateurs/nouveau", methods=["GET", "POST"])
@login_required
@ACCES_ADMIN
def creer_utilisateur():
    form = UtilisateurForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if Utilisateur.query.filter_by(email=email).first():
            flash("Un compte utilise déjà cet e-mail.", "error")
        elif not form.mot_de_passe.data:
            flash("Le mot de passe est requis à la création (8 caractères min.).", "error")
        else:
            utilisateur = Utilisateur(
                nom=form.nom.data.strip(),
                email=email,
                role=form.role.data,
                actif=form.actif.data,
                point_de_vente_id=current_user.point_de_vente_id,
            )
            utilisateur.definir_mot_de_passe(form.mot_de_passe.data)
            db.session.add(utilisateur)
            db.session.commit()
            flash("Utilisateur créé.", "success")
            return redirect(url_for("admin.index"))
    return render_template("admin/utilisateur_form.html", form=form, mode="creer")


@bp.route("/utilisateurs/<int:id_utilisateur>/editer", methods=["GET", "POST"])
@login_required
@ACCES_ADMIN
def editer_utilisateur(id_utilisateur):
    utilisateur = db.session.get(Utilisateur, id_utilisateur) or abort(404)
    form = UtilisateurForm(obj=utilisateur)
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existant = Utilisateur.query.filter_by(email=email).first()
        if existant and existant.id_utilisateur != utilisateur.id_utilisateur:
            flash("Un autre compte utilise déjà cet e-mail.", "error")
        else:
            utilisateur.nom = form.nom.data.strip()
            utilisateur.email = email
            utilisateur.role = form.role.data
            utilisateur.actif = form.actif.data
            if form.mot_de_passe.data:  # optionnel en édition
                utilisateur.definir_mot_de_passe(form.mot_de_passe.data)
            db.session.commit()
            flash("Utilisateur mis à jour.", "success")
            return redirect(url_for("admin.index"))
    return render_template(
        "admin/utilisateur_form.html", form=form, mode="editer", utilisateur=utilisateur
    )


@bp.route("/utilisateurs/<int:id_utilisateur>/supprimer", methods=["POST"])
@login_required
@ACCES_ADMIN
def supprimer_utilisateur(id_utilisateur):
    form = ConfirmationForm()
    if not form.validate_on_submit():
        abort(400)
    utilisateur = db.session.get(Utilisateur, id_utilisateur) or abort(404)
    # On empêche de supprimer son propre compte depuis le back-office
    # (passerait par « Mon compte »), pour éviter de se verrouiller.
    if utilisateur.id_utilisateur == current_user.id_utilisateur:
        flash("Utilisez « Mon compte » pour supprimer votre propre compte.", "warning")
        return redirect(url_for("admin.index"))
    db.session.delete(utilisateur)
    db.session.commit()
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for("admin.index"))


@bp.route("/reinitialiser-demo", methods=["POST"])
@login_required
@role_requis(ROLE_MANAGER)  # action sensible : réservée au manager
def reinitialiser_demo():
    """Repart d'un jeu de données de démonstration propre.

    Utile avant une démonstration, et pour repartir sur des indicateurs justes
    si des imports répétés ont faussé l'historique. Les comptes de démonstration
    sont recréés à l'identique : la session courante est donc fermée et il faut
    se reconnecter.
    """
    form = ConfirmationForm()
    if not form.validate_on_submit():
        abort(400)

    from scripts.seed import executer_seed

    executer_seed()
    logout_user()
    flash(
        "Données de démonstration réinitialisées. Reconnectez-vous pour continuer.",
        "success",
    )
    return redirect(url_for("auth.login"))
