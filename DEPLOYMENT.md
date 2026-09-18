# AWS EC2 deployment

The production deployment uses Docker Compose. The frontend image builds the
Vue application and serves it through Nginx. Nginx proxies `/api`, `/docs`, and
`/openapi.json` to the private API container. PostgreSQL and Redis are not
published to the internet.

## Required EC2 setup

- Ubuntu 22.04 or newer
- Docker Engine with the Compose v2 plugin
- An EC2 security group allowing SSH (22) from your IP and HTTP (80) publicly
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
Visit `http://EC2_PUBLIC_IP/` after all containers report healthy.

## Updating

```bash
cd ~/fixmypdf
git pull --ff-only
docker compose up --build -d
docker image prune -f
```

## Logs and health

```bash
docker compose ps
docker compose logs --tail=200 api worker frontend
curl --fail http://127.0.0.1/api/health/
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
