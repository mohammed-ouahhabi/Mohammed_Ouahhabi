"""ajout table vente (Pulse)

Revision ID: 7e82ed7716eb
Revises: 4b8012d89dd8
Create Date: 2026-07-15 21:37:49.993643

Migration défensive : elle vérifie l'état réel de la base avant d'agir. Une base
peut posséder les tables sans que le registre Alembic soit à jour — c'est le cas
lorsqu'elle a été créée par `create_all()` plutôt que par les migrations. Sans
cette précaution, la migration échoue sur « table vente already exists » et
TOUTES les migrations suivantes restent inappliquées : le schéma demeure
incomplet et les écrans réclamant les colonnes manquantes renvoient une erreur.

Les vérifications reposent sur l'inspecteur SQLAlchemy : elles fonctionnent
indifféremment sur SQLite (développement) et PostgreSQL (production).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e82ed7716eb'
down_revision = '4b8012d89dd8'
branch_labels = None
depends_on = None


def _table_existe(nom):
    return sa.inspect(op.get_bind()).has_table(nom)


def upgrade():
    if _table_existe('vente'):
        return  # déjà en place : on n'interrompt pas la chaîne de migrations

    op.create_table('vente',
    sa.Column('id_vente', sa.Integer(), nullable=False),
    sa.Column('commande_id', sa.Integer(), nullable=False),
    sa.Column('montant', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('mode_paiement', sa.String(length=40), nullable=True),
    sa.Column('date_vente', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['commande_id'], ['commande.id_commande'], ),
    sa.PrimaryKeyConstraint('id_vente')
    )


def downgrade():
    if _table_existe('vente'):
        op.drop_table('vente')
