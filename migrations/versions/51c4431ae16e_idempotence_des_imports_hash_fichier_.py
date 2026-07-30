"""idempotence des imports (hash fichier + cle ligne + ignorees)

Revision ID: 51c4431ae16e
Revises: 7e82ed7716eb
Create Date: 2026-07-28 04:03:12.811683

Migration défensive : chaque colonne et chaque index ne sont créés que s'ils sont
absents. Une base dont le registre Alembic est désynchronisé peut en effet déjà
les posséder ; sans cette précaution, la migration échouerait et laisserait le
schéma dans un état intermédiaire.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51c4431ae16e'
down_revision = '7e82ed7716eb'
branch_labels = None
depends_on = None


def _colonnes(table):
    inspecteur = sa.inspect(op.get_bind())
    if not inspecteur.has_table(table):
        return set()
    return {c["name"] for c in inspecteur.get_columns(table)}


def _index(table):
    inspecteur = sa.inspect(op.get_bind())
    if not inspecteur.has_table(table):
        return set()
    return {i["name"] for i in inspecteur.get_indexes(table)}


def upgrade():
    colonnes = _colonnes('import_fichier')
    index = _index('import_fichier')
    with op.batch_alter_table('import_fichier', schema=None) as batch_op:
        if 'lignes_ignorees' not in colonnes:
            # server_default='0' est indispensable : la table contient déjà des
            # lignes en production, et une colonne NOT NULL sans valeur par
            # défaut ferait échouer la migration sur PostgreSQL.
            batch_op.add_column(
                sa.Column('lignes_ignorees', sa.Integer(), nullable=False, server_default='0')
            )
        if 'hash_fichier' not in colonnes:
            batch_op.add_column(sa.Column('hash_fichier', sa.String(length=64), nullable=True))
        if 'ix_import_fichier_hash_fichier' not in index:
            batch_op.create_index(
                batch_op.f('ix_import_fichier_hash_fichier'), ['hash_fichier'], unique=False
            )

    colonnes = _colonnes('ligne_commande')
    index = _index('ligne_commande')
    with op.batch_alter_table('ligne_commande', schema=None) as batch_op:
        if 'cle_idempotence' not in colonnes:
            batch_op.add_column(sa.Column('cle_idempotence', sa.String(length=64), nullable=True))
        if 'ix_ligne_commande_cle_idempotence' not in index:
            batch_op.create_index(
                batch_op.f('ix_ligne_commande_cle_idempotence'), ['cle_idempotence'], unique=True
            )


def downgrade():
    colonnes = _colonnes('ligne_commande')
    index = _index('ligne_commande')
    with op.batch_alter_table('ligne_commande', schema=None) as batch_op:
        if 'ix_ligne_commande_cle_idempotence' in index:
            batch_op.drop_index(batch_op.f('ix_ligne_commande_cle_idempotence'))
        if 'cle_idempotence' in colonnes:
            batch_op.drop_column('cle_idempotence')

    colonnes = _colonnes('import_fichier')
    index = _index('import_fichier')
    with op.batch_alter_table('import_fichier', schema=None) as batch_op:
        if 'ix_import_fichier_hash_fichier' in index:
            batch_op.drop_index(batch_op.f('ix_import_fichier_hash_fichier'))
        if 'hash_fichier' in colonnes:
            batch_op.drop_column('hash_fichier')
        if 'lignes_ignorees' in colonnes:
            batch_op.drop_column('lignes_ignorees')
