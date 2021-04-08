import sqlalchemy

metadata = sqlalchemy.MetaData()

SignedStatement = sqlalchemy.Table(
    'signed_statement',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('title', sqlalchemy.String(length=100)),
    sqlalchemy.Column('author', sqlalchemy.String(length=60)),)
