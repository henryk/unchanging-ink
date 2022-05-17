"""initial

Revision ID: 58d9beb8eff9
Revises: 
Create Date: 2022-05-17 15:37:28.911928

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '58d9beb8eff9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('interval',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('timestamp', sa.String(length=32), nullable=False),
    sa.Column('itmh', sa.LargeBinary(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('timestamp',
    sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('timestamp', sa.String(length=32), nullable=False),
    sa.Column('hash', sa.LargeBinary(length=64), nullable=False),
    sa.Column('tag', sa.String(length=36), nullable=True),
    sa.Column('interval', sa.BigInteger(), nullable=True),
    sa.Column('proof', sa.LargeBinary(), nullable=True),
    sa.ForeignKeyConstraint(['interval'], ['interval.id'], deferrable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timestamp_interval'), 'timestamp', ['interval'], unique=False)
    op.create_index(op.f('ix_timestamp_tag'), 'timestamp', ['tag'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_timestamp_tag'), table_name='timestamp')
    op.drop_index(op.f('ix_timestamp_interval'), table_name='timestamp')
    op.drop_table('timestamp')
    op.drop_table('interval')
    # ### end Alembic commands ###
