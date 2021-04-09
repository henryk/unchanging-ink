import sqlalchemy
from sqlalchemy_utils.types import uuid

metadata = sqlalchemy.MetaData()

signed_timestamp = sqlalchemy.Table(
    "signed_timestamp",
    metadata,
    sqlalchemy.Column("id", uuid.UUIDType, primary_key=True),
    sqlalchemy.Column("kid", sqlalchemy.String(length=128), nullable=False),
    sqlalchemy.Column("timestamp", sqlalchemy.String(length=32), nullable=False),
    sqlalchemy.Column("signature", sqlalchemy.LargeBinary(length=64), nullable=False),
    sqlalchemy.Column(
        "interval",
        sqlalchemy.BigInteger,
        sqlalchemy.ForeignKey("interval.id"),
        nullable=True,
    ),
    sqlalchemy.Column("proof", sqlalchemy.JSON(), nullable=True),
)

interval = sqlalchemy.Table(
    "interval",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column("ith", sqlalchemy.LargeBinary(length=64), nullable=False),
)
