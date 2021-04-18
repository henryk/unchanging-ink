import sqlalchemy
from sqlalchemy_utils.types import uuid

metadata = sqlalchemy.MetaData()

signed_timestamp = sqlalchemy.Table(
    "signed_timestamp",
    metadata,
    sqlalchemy.Column("id", uuid.UUIDType, primary_key=True),
    sqlalchemy.Column("kid", sqlalchemy.String(length=128), nullable=False),
    sqlalchemy.Column("timestamp", sqlalchemy.String(length=32), nullable=False),
    sqlalchemy.Column("signature", sqlalchemy.LargeBinary(length=64), nullable=False)
)

timestamp_proof = sqlalchemy.Table(
    'timestamp_proof',
    metadata,
    sqlalchemy.Column("id", uuid.UUIDType, sqlalchemy.ForeignKey("signed_timestamp.id", deferrable=True), primary_key=True, nullable=False),
    sqlalchemy.Column(
        "interval",
        sqlalchemy.BigInteger,
        sqlalchemy.ForeignKey("interval.id", deferrable=True),
        nullable=False,
    ),
    sqlalchemy.Column("proof", sqlalchemy.JSON(), nullable=False),
)

interval = sqlalchemy.Table(
    "interval",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column("ith", sqlalchemy.LargeBinary(length=64), nullable=False),
)

node = sqlalchemy.Table(
    "node",
    metadata,
    sqlalchemy.Column("start", sqlalchemy.BigInteger, nullable=False),
    sqlalchemy.Column("end", sqlalchemy.BigInteger, nullable=False),
    sqlalchemy.Column("value", sqlalchemy.LargeBinary(length=64), nullable=False),
    sqlalchemy.PrimaryKeyConstraint("start", "end", name="node_pk"),
)
