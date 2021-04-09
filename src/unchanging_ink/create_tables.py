import sqlalchemy

from .server import db
from .models import metadata

def main():
    engine = sqlalchemy.create_engine(str(db.url))
    metadata.drop_all(engine)
    metadata.create_all(engine)


if __name__ == "__main__":
    main()
