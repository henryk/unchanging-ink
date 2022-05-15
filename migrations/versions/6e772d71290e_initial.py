"""initial

Revision ID: 6e772d71290e
Revises: 
Create Date: 2022-05-15 22:47:49.382437

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "6e772d71290e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "interval",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("timestamp", sa.String(length=32), nullable=False),
        sa.Column("itmh", sa.LargeBinary(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "timestamp",
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("timestamp", sa.String(length=32), nullable=False),
        sa.Column("hash", sa.LargeBinary(length=64), nullable=False),
        sa.Column("tag", sa.String(length=36), nullable=True),
        sa.Column("interval", sa.BigInteger(), nullable=True),
        sa.Column("proof", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["interval"], ["interval.id"], deferrable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_timestamp_interval"), "timestamp", ["interval"], unique=False
    )
    op.create_index(op.f("ix_timestamp_tag"), "timestamp", ["tag"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_timestamp_tag"), table_name="timestamp")
    op.drop_index(op.f("ix_timestamp_interval"), table_name="timestamp")
    op.drop_table("timestamp")
    op.drop_table("interval")
    # ### end Alembic commands ###
