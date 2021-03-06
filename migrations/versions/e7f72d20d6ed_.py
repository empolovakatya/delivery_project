"""empty message

Revision ID: e7f72d20d6ed
Revises: 6e72a617587c
Create Date: 2020-07-24 16:35:44.240643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f72d20d6ed'
down_revision = '6e72a617587c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('meals', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'meals')
    # ### end Alembic commands ###
