"""Add status column to User table

Revision ID: 4bdf3d69c4a5
Revises: 780f410de5fe
Create Date: 2025-02-26 18:29:41.458187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bdf3d69c4a5'
down_revision = '780f410de5fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
