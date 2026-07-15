"""Modèles SQLAlchemy.

Ils reproduisent fidèlement le schéma relationnel fourni :
    point_de_vente, utilisateur, produit, commande, ligne_commande, import_fichier

Seule addition par rapport au MLD métier : la colonne `mot_de_passe_hash` sur
`utilisateur`. Elle est indispensable à l'authentification (on ne stocke jamais
le mot de passe en clair) et ne fait pas partie des données métier — c'est une
contrainte technique de sécurité, pas un écart avec le modèle.
"""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager


# --------------------------------------------------------------------------
# Rôles applicatifs
# --------------------------------------------------------------------------
# Les valeurs stockées en base sont des identifiants stables (jamais traduits).
# ROLE_LABELS donne le libellé affiché à l'écran.
ROLE_MANAGER = "manager"
ROLE_ASSISTANT = "assistant"
ROLE_PREMIER_EQUIPIER = "premier_equipier"
ROLE_EQUIPIER = "equipier"

ROLE_LABELS = {
    ROLE_MANAGER: "Manager",
    ROLE_ASSISTANT: "Assistant manager",
    ROLE_PREMIER_EQUIPIER: "Premier équipier",
    ROLE_EQUIPIER: "Équipier",
}

# Rôles autorisés à accéder au back-office (administration + import).
ROLES_BACK_OFFICE = {ROLE_MANAGER, ROLE_ASSISTANT}
# Rôles autorisés à consulter l'analyse des ventes.
ROLES_ANALYSE = {ROLE_MANAGER, ROLE_ASSISTANT, ROLE_PREMIER_EQUIPIER}


class PointDeVente(db.Model):
    __tablename__ = "point_de_vente"

    id_point_de_vente = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    ville = db.Column(db.String(120), nullable=False)

    utilisateurs = db.relationship("Utilisateur", back_populates="point_de_vente")
    commandes = db.relationship("Commande", back_populates="point_de_vente")

    def __repr__(self):
        return f"<PointDeVente {self.nom}>"


class Utilisateur(UserMixin, db.Model):
    __tablename__ = "utilisateur"

    id_utilisateur = db.Column(db.Integer, primary_key=True)
    point_de_vente_id = db.Column(
        db.Integer, db.ForeignKey("point_de_vente.id_point_de_vente"), nullable=True
    )
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    role = db.Column(db.String(40), nullable=False, default=ROLE_EQUIPIER)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    # Colonne technique (hors MLD métier) : hachage du mot de passe.
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)

    point_de_vente = db.relationship("PointDeVente", back_populates="utilisateurs")
    imports = db.relationship("ImportFichier", back_populates="utilisateur")

    # -- Authentification ---------------------------------------------------
    def definir_mot_de_passe(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def verifier_mot_de_passe(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    # Flask-Login attend une propriété `id`. Notre clé s'appelle
    # id_utilisateur : on l'expose via get_id().
    def get_id(self):
        return str(self.id_utilisateur)

    @property
    def is_active(self):
        # Un compte désactivé ne peut pas se connecter (Flask-Login).
        return bool(self.actif)

    # -- Contrôle d'accès (utilisé par les décorateurs et les templates) ----
    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)

    def a_role(self, *roles):
        return self.role in roles

    @property
    def peut_administrer(self):
        return self.role in ROLES_BACK_OFFICE

    @property
    def peut_analyser(self):
        return self.role in ROLES_ANALYSE

    def __repr__(self):
        return f"<Utilisateur {self.email} ({self.role})>"


class Produit(db.Model):
    __tablename__ = "produit"

    id_produit = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    categorie = db.Column(db.String(80), nullable=True)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    lignes = db.relationship("LigneCommande", back_populates="produit")

    def __repr__(self):
        return f"<Produit {self.nom}>"


class Commande(db.Model):
    __tablename__ = "commande"

    id_commande = db.Column(db.Integer, primary_key=True)
    point_de_vente_id = db.Column(
        db.Integer, db.ForeignKey("point_de_vente.id_point_de_vente"), nullable=False
    )
    date_heure = db.Column(db.DateTime, nullable=False, index=True)
    montant_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    point_de_vente = db.relationship("PointDeVente", back_populates="commandes")
    lignes = db.relationship(
        "LigneCommande", back_populates="commande", cascade="all, delete-orphan"
    )
    ventes = db.relationship(
        "Vente", back_populates="commande", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Commande {self.id_commande} le {self.date_heure}>"


class LigneCommande(db.Model):
    __tablename__ = "ligne_commande"

    id_ligne_commande = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(
        db.Integer, db.ForeignKey("commande.id_commande"), nullable=False
    )
    produit_id = db.Column(
        db.Integer, db.ForeignKey("produit.id_produit"), nullable=False
    )
    quantite = db.Column(db.Integer, nullable=False, default=1)
    montant = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    commande = db.relationship("Commande", back_populates="lignes")
    produit = db.relationship("Produit", back_populates="lignes")

    def __repr__(self):
        return f"<LigneCommande {self.id_ligne_commande}>"


class Vente(db.Model):
    """Encaissement d'une commande (issu du système source Pulse de Domino's).

    Porte le mode de paiement, absent du reste du modèle. IMPORTANT : cette table
    ne sert JAMAIS au calcul du chiffre d'affaires (toujours issu de
    ligne_commande, source unique de vérité). `montant` reflète l'encaissement et
    doit rester cohérent avec commande.montant_total.
    """

    __tablename__ = "vente"

    id_vente = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(
        db.Integer, db.ForeignKey("commande.id_commande"), nullable=False
    )
    montant = db.Column(db.Numeric(10, 2), nullable=False)
    mode_paiement = db.Column(db.String(40), nullable=True)
    date_vente = db.Column(db.DateTime, nullable=False)

    commande = db.relationship("Commande", back_populates="ventes")

    def __repr__(self):
        return f"<Vente {self.id_vente} ({self.mode_paiement})>"


class ImportFichier(db.Model):
    __tablename__ = "import_fichier"

    id_import = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    nom_fichier = db.Column(db.String(255), nullable=False)
    date_import = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lignes_lues = db.Column(db.Integer, nullable=False, default=0)
    lignes_rejetees = db.Column(db.Integer, nullable=False, default=0)
    statut = db.Column(db.String(40), nullable=False, default="en_cours")

    utilisateur = db.relationship("Utilisateur", back_populates="imports")

    @property
    def lignes_integrees(self):
        return self.lignes_lues - self.lignes_rejetees

    def __repr__(self):
        return f"<ImportFichier {self.nom_fichier} ({self.statut})>"


# Flask-Login : recharge l'utilisateur à partir de l'id stocké en session.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Utilisateur, int(user_id))
