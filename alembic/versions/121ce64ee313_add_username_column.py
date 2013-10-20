"""Add username column

Revision ID: 121ce64ee313
Revises: None
Create Date: 2013-10-20 18:49:43.605318

"""

# revision identifiers, used by Alembic.
revision = '121ce64ee313'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("users", sa.Column("username", sa.String))


def downgrade():
    op.drop_column("users", "username")
