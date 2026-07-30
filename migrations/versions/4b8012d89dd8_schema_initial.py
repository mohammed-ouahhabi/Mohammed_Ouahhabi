"""schema initial

Revision ID: 4b8012d89dd8
Revises:
Create Date: 2026-07-08 01:43:00.000000

Migration défensive : chaque table n'est créée que si elle est absente. Une base
créée par `create_all()` plutôt que par les migrations possède déjà ces tables
sans que le registre Alembic le sache ; sans cette précaution, la migration
échouerait dès la première table et bloquerait toute la chaîne.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b8012d89dd8'
down_revision = None
branch_labels = None
depends_on = None


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade():
    existantes = _tables()

    if 'point_de_vente' not in existantes:
        op.create_table('point_de_vente',
        sa.Column('id_point_de_vente', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=120), nullable=False),
        sa.Column('ville', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id_point_de_vente')
        )

    if 'produit' not in existantes:
        op.create_table('produit',
        sa.Column('id_produit', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=120), nullable=False),
        sa.Column('categorie', sa.String(length=80), nullable=True),
        sa.Column('prix_unitaire', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('id_produit')
        )

    if 'commande' not in existantes:
        op.create_table('commande',
        sa.Column('id_commande', sa.Integer(), nullable=False),
        sa.Column('point_de_vente_id', sa.Integer(), nullable=False),
        sa.Column('date_heure', sa.DateTime(), nullable=False),
        sa.Column('montant_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['point_de_vente_id'], ['point_de_vente.id_point_de_vente'], ),
        sa.PrimaryKeyConstraint('id_commande')
        )
        with op.batch_alter_table('commande', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_commande_date_heure'), ['date_heure'], unique=False)

    if 'utilisateur' not in existantes:
        op.create_table('utilisateur',
        sa.Column('id_utilisateur', sa.Integer(), nullable=False),
        sa.Column('point_de_vente_id', sa.Integer(), nullable=True),
        sa.Column('nom', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=180), nullable=False),
        sa.Column('role', sa.String(length=40), nullable=False),
        sa.Column('actif', sa.Boolean(), nullable=False),
        sa.Column('mot_de_passe_hash', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['point_de_vente_id'], ['point_de_vente.id_point_de_vente'], ),
        sa.PrimaryKeyConstraint('id_utilisateur')
        )
        with op.batch_alter_table('utilisateur', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_utilisateur_email'), ['email'], unique=True)

    if 'import_fichier' not in existantes:
        op.create_table('import_fichier',
        sa.Column('id_import', sa.Integer(), nullable=False),
        sa.Column('utilisateur_id', sa.Integer(), nullable=False),
        sa.Column('nom_fichier', sa.String(length=255), nullable=False),
        sa.Column('date_import', sa.DateTime(), nullable=False),
        sa.Column('lignes_lues', sa.Integer(), nullable=False),
        sa.Column('lignes_rejetees', sa.Integer(), nullable=False),
        sa.Column('statut', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id_utilisateur'], ),
        sa.PrimaryKeyConstraint('id_import')
        )

    if 'ligne_commande' not in existantes:
        op.create_table('ligne_commande',
        sa.Column('id_ligne_commande', sa.Integer(), nullable=False),
        sa.Column('commande_id', sa.Integer(), nullable=False),
        sa.Column('produit_id', sa.Integer(), nullable=False),
        sa.Column('quantite', sa.Integer(), nullable=False),
        sa.Column('montant', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['commande_id'], ['commande.id_commande'], ),
        sa.ForeignKeyConstraint(['produit_id'], ['produit.id_produit'], ),
        sa.PrimaryKeyConstraint('id_ligne_commande')
        )


def downgrade():
    existantes = _tables()

    # Ordre inverse des dépendances de clés étrangères.
    if 'ligne_commande' in existantes:
        op.drop_table('ligne_commande')
    if 'import_fichier' in existantes:
        op.drop_table('import_fichier')
    if 'utilisateur' in existantes:
        with op.batch_alter_table('utilisateur', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_utilisateur_email'))
        op.drop_table('utilisateur')
    if 'commande' in existantes:
        with op.batch_alter_table('commande', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_commande_date_heure'))
        op.drop_table('commande')
    if 'produit' in existantes:
        op.drop_table('produit')
    if 'point_de_vente' in existantes:
        op.drop_table('point_de_vente')
