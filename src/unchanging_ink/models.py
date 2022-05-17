import sqlalchemy
from sqlalchemy_utils.types import uuid

metadata = sqlalchemy.MetaData()

timestamp = sqlalchemy.Table(
    "timestamp",
    metadata,
    sqlalchemy.Column("id", uuid.UUIDType, primary_key=True),
    sqlalchemy.Column("timestamp", sqlalchemy.String(length=32), nullable=False),
    sqlalchemy.Column("hash", sqlalchemy.LargeBinary(length=64), nullable=False),
    sqlalchemy.Column(
        "tag",
        sqlalchemy.String(length=36),
        nullable=True,
        index=True,
    ),
    sqlalchemy.Column(
        "interval",
        sqlalchemy.BigInteger,
        sqlalchemy.ForeignKey("interval.id", deferrable=True),
        nullable=True,
        index=True,
    ),
    sqlalchemy.Column("proof", sqlalchemy.LargeBinary(), nullable=True),
)

interval = sqlalchemy.Table(
    "interval",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column("timestamp", sqlalchemy.String(length=32), nullable=False),
    sqlalchemy.Column("itmh", sqlalchemy.LargeBinary(length=64), nullable=False),
)
