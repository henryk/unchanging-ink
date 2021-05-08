# Deployment

The `docker-compose.yml` file, in combination with `.env` provides a full deployment behind an nginx reverse proxy.
For custom deployment options you need to create a copy of the `.env` file and pass it to `docker-compose` (which doesn't support multiple env files and overrides).

Example:

````bash
cp .env .env.local
nano .env.local
docker-compose --env-file=.env.local up -d
````

The deployment will expose a single port (23230 by default) which will contain both the frontend and backend (mounted under /api/).
