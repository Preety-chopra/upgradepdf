# AWS EC2 deployment

The production deployment uses Docker Compose. Caddy is the public edge server:
it obtains and renews the TLS certificate for `upgradepdf.com`, redirects HTTP
to HTTPS, and proxies requests to the private frontend container. The frontend
image builds the Vue application and serves it through Nginx. Nginx proxies
`/api`, `/docs`, and `/openapi.json` to the private API container. PostgreSQL
and Redis are not published to the internet.

The root `Dockerfile` contains separate `backend`, `frontend-development`, and
`frontend-production` build targets. Docker Compose selects the correct target
for each service; there are no Dockerfiles inside `backend/` or `frontend/`.

## Required EC2 setup

- Ubuntu 22.04 or newer
- Docker Engine with the Compose v2 plugin
- DNS `A` record for `upgradepdf.com` pointing to the EC2 public IPv4 address
- An EC2 security group allowing SSH (22) from your IP and TCP 80 and 443
  publicly. TCP 80 must remain open for the automatic HTTP-to-HTTPS redirect
  and ACME certificate validation. UDP 443 is optional and enables HTTP/3.
- At least 4 GB RAM recommended for OCR and LibreOffice conversions

## First deployment

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Sign out and back in after adding the Docker group, then clone and configure:

```bash
git clone https://github.com/Preety-chopra/fixmypdf.git
cd fixmypdf
cp .env.example .env
nano .env
docker compose config
docker compose up --build -d
docker compose ps
```

Replace `POSTGRES_PASSWORD` in `.env` before starting. Do not commit `.env`.
Visit `https://upgradepdf.com/` after all containers report healthy. On the
first start, Caddy requests the certificate automatically; follow its logs if
HTTPS is not ready after a minute:

```bash
docker compose logs --tail=200 caddy
```

## Updating

```bash
cd ~/fixmypdf
git pull --ff-only
docker compose up --build -d
docker image prune -f
```

## Deploying prebuilt Docker Hub images

Use one Docker Hub repository with separate `backend` and `frontend` tags. Set
`BACKEND_IMAGE` and `FRONTEND_IMAGE` in the EC2 `.env`, then deploy without
building on the instance:

```bash
docker compose pull
docker compose up -d --no-build
```

## Google Analytics

The shared `frontend/index.html` template installs Google tag
`G-GYKQ5QGVQD` once per page. The production build carries the tag into every
generated route page; rebuild and deploy the frontend for changes to take effect.

In Google Analytics, select this website's web stream under **Admin > Data
streams**. Enable **Enhanced measurement > Page views > Show advanced settings >
Page changes based on browser history events** so navigation between Vue tools
is recorded. Page views use Google's automatic measurement; do not add a second
tag or manual router page-view events.

After deployment, visit the homepage and navigate to a few tools. Check the
**Realtime** report for activity, and use **DebugView** with debug mode enabled
to confirm each navigation produces one `page_view` with the expected page URL.
Initial collection can take up to 30 minutes. Analytics collects visits from the
time the tag is installed; it does not backfill earlier visits.

Setup reference: https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications

## Logs and health

```bash
docker compose ps
docker compose logs --tail=200 api worker frontend caddy
curl --fail --resolve upgradepdf.com:443:127.0.0.1 https://upgradepdf.com/api/health/
```

## Development override

For bind mounts, API reload, Vite, and exposed development ports:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Data and backups

The `postgres_data`, `redis_data`, and `pdf_storage` named volumes persist
across container recreation. Back up the PostgreSQL volume/database before
upgrading or replacing the EC2 instance. Deleting volumes with
`docker compose down --volumes` permanently deletes application data.
