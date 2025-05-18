"""Add user_id to Trip model

Revision ID: 75f3adce98c5
Revises: 3d588e1955f4
Create Date: 2025-02-27 12:26:49.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '75f3adce98c5'
down_revision = '3d588e1955f4'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'))
        batch_op.create_foreign_key('fk_trip_user_id', 'user', ['user_id'], ['id'])

    # Remove the default value after the column has been added and populated
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.alter_column('user_id', server_default=None)

def downgrade():
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_constraint('fk_trip_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')