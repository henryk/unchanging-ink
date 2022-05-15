# Unchanging.Ink -- Merkle Tree Timestamping Service

## Development notes

To create database migrations use alembic in docker:

````
docker-compose -f .\docker-compose.yml -f .\docker-compose.dev.yml run --rm worker sh -c 'poetry install -E worker && poetry run alembic revision --autogenerate -m initial'
````

