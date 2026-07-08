"""Formulaires Flask-WTF.

Chaque formulaire embarque automatiquement un jeton CSRF (protection contre la
falsification de requête) rendu dans les templates via `form.hidden_tag()`.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

from .models import ROLE_LABELS


class LoginForm(FlaskForm):
    email = StringField(
        "Adresse e-mail",
        validators=[DataRequired(message="L'e-mail est requis."), Email()],
    )
    mot_de_passe = PasswordField(
        "Mot de passe", validators=[DataRequired(message="Le mot de passe est requis.")]
    )
    se_souvenir = BooleanField("Se souvenir de moi")
    submit = SubmitField("Se connecter")


def _choix_roles():
    return [(cle, libelle) for cle, libelle in ROLE_LABELS.items()]


class UtilisateurForm(FlaskForm):
    """Création / édition d'un utilisateur (back-office)."""

    nom = StringField("Nom", validators=[DataRequired(), Length(max=120)])
    email = StringField("Adresse e-mail", validators=[DataRequired(), Email(), Length(max=180)])
    role = SelectField("Rôle", choices=_choix_roles, validators=[DataRequired()])
    actif = BooleanField("Compte actif", default=True)
    # Mot de passe optionnel en édition (laisser vide = inchangé),
    # requis à la création — la vue s'en assure.
    mot_de_passe = PasswordField("Mot de passe", validators=[Optional(), Length(min=8)])
    submit = SubmitField("Enregistrer")


class ProfilForm(FlaskForm):
    """Modification de son propre compte (RGPD : droit de rectification)."""

    nom = StringField("Nom", validators=[DataRequired(), Length(max=120)])
    email = StringField("Adresse e-mail", validators=[DataRequired(), Email(), Length(max=180)])
    mot_de_passe = PasswordField(
        "Nouveau mot de passe (laisser vide pour ne pas changer)",
        validators=[Optional(), Length(min=8)],
    )
    confirmation = PasswordField(
        "Confirmer le mot de passe",
        validators=[Optional(), EqualTo("mot_de_passe", message="Les mots de passe ne correspondent pas.")],
    )
    submit = SubmitField("Enregistrer mes modifications")


class ImportForm(FlaskForm):
    """Upload d'un fichier CSV pour le pipeline."""

    fichier = FileField(
        "Fichier CSV",
        validators=[
            FileRequired(message="Veuillez sélectionner un fichier."),
            FileAllowed(["csv"], message="Seuls les fichiers CSV sont acceptés."),
        ],
    )
    submit = SubmitField("Analyser le fichier")


class ConfirmationForm(FlaskForm):
    """Formulaire minimal (jeton CSRF) pour les actions POST simples :
    suppression d'utilisateur, suppression de son propre compte, etc."""

    submit = SubmitField("Confirmer")
