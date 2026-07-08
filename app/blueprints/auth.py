"""Authentification et gestion de son propre compte (Flask-Login)."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..forms import LoginForm, ProfilForm, ConfirmationForm
from ..models import Utilisateur

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Un utilisateur déjà connecté est renvoyé vers le tableau de bord.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        utilisateur = Utilisateur.query.filter_by(email=form.email.data.lower().strip()).first()
        if utilisateur is None or not utilisateur.verifier_mot_de_passe(form.mot_de_passe.data):
            flash("E-mail ou mot de passe incorrect.", "error")
        elif not utilisateur.actif:
            flash("Ce compte est désactivé. Contactez un administrateur.", "error")
        else:
            login_user(utilisateur, remember=form.se_souvenir.data)
            # Redirection sûre : on n'accepte que les chemins internes.
            suivant = request.args.get("next")
            if not suivant or not suivant.startswith("/"):
                suivant = url_for("dashboard.index")
            return redirect(suivant)
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/mon-compte", methods=["GET", "POST"])
@login_required
def mon_compte():
    """RGPD : droit de rectification. L'utilisateur modifie ses infos / mot de passe."""
    form = ProfilForm(obj=current_user)
    suppression_form = ConfirmationForm()
    if form.validate_on_submit():
        nouvel_email = form.email.data.lower().strip()
        # Empêche de prendre l'e-mail d'un autre compte.
        existant = Utilisateur.query.filter_by(email=nouvel_email).first()
        if existant and existant.id_utilisateur != current_user.id_utilisateur:
            flash("Cet e-mail est déjà utilisé par un autre compte.", "error")
        else:
            current_user.nom = form.nom.data.strip()
            current_user.email = nouvel_email
            if form.mot_de_passe.data:
                current_user.definir_mot_de_passe(form.mot_de_passe.data)
            db.session.commit()
            flash("Vos informations ont été mises à jour.", "success")
            return redirect(url_for("auth.mon_compte"))
    return render_template(
        "auth/mon_compte.html", form=form, suppression_form=suppression_form
    )


@bp.route("/mon-compte/supprimer", methods=["POST"])
@login_required
def supprimer_mon_compte():
    """RGPD : droit à l'effacement de son propre compte."""
    form = ConfirmationForm()
    if form.validate_on_submit():
        utilisateur = current_user._get_current_object()
        logout_user()
        db.session.delete(utilisateur)
        db.session.commit()
        flash("Votre compte a été supprimé.", "success")
        return redirect(url_for("auth.login"))
    return redirect(url_for("auth.mon_compte"))
