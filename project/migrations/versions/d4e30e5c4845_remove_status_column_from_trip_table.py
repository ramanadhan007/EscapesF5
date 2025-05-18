"""Remove status column from Trip table

Revision ID: d4e30e5c4845
Revises: 94099dbbe346
Create Date: 2025-02-26 17:57:20.041819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e30e5c4845'
down_revision = '94099dbbe346'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the status column from the Trip table
    with op.batch_alter_table('trip') as batch_op:
        batch_op.drop_column('status')


def downgrade():
    # Add the status column back to the Trip table
    with op.batch_alter_table('trip') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=True))