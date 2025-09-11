# Student API – Linux Setup & Make Targets

This README gives **copy‑pasteable** Linux setup (with tiny bash installer functions), required tools, environment setup, the **exact order** to run `make` targets, and how volumes are laid out. It’s designed so any teammate can get from zero → running API quickly.

---

## TL;DR (Quickstart)

1. **Install tools** (Docker + Make) — copy the installer functions below, then run:

   ```bash
   install_docker && install_make && install_git && install_curl && install_jq
   newgrp docker  # re‑eval group so docker works without reboot
   ```
2. **Clone & configure**:

   ```bash
   git clone <YOUR_REPO_URL> student-api && cd student-api
   cp .env .env.local  # optional: keep a local copy to tweak
   ```
3. **Run in correct order** (details below):

   ```bash
   make docker-build
   make up
   make migrate  # create/refresh migration (if you changed models)
   make upgrade  # apply DB schema
   make logs     # watch logs; Ctrl+C to exit
   ```
4. **Hit health**:

   ```bash
   curl -i http://localhost:5000/api/v2/health
   curl -i http://localhost:5000/api/v2/db/health
   ```

> Default API base path: **`/api/v2`**

---

## Pre‑requisites (Linux only)

These tiny **bash functions** install everything on Debian/Ubuntu‑like systems. **Copy this whole block** into your terminal and run whichever you need.

```bash
set -e

install_docker() {
  echo "[+] Installing Docker Engine (root required)"
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
  sudo systemctl enable --now docker
  echo "[✓] Docker installed. You may need 'newgrp docker' or re-login for group change to take effect."
}

install_make() {
  echo "[+] Installing GNU make"
  sudo apt-get update -y
  sudo apt-get install -y make
}

install_git() {
  echo "[+] Installing git"
  sudo apt-get update -y
  sudo apt-get install -y git
}

install_curl() {
  echo "[+] Installing curl"
  sudo apt-get update -y
  sudo apt-get install -y curl
}

install_jq() {
  echo "[+] Installing jq (optional but handy)"
  sudo apt-get update -y
  sudo apt-get install -y jq
}

verify_tools() {
  echo "[?] Verifying tools"
  command -v docker && docker --version
  command -v docker compose && docker compose version
  command -v make && make --version | head -n1
  command -v curl && curl --version | head -n1
  command -v jq && jq --version || echo "jq not found (optional)"
  echo "[✓] Verification done"
}
```

**Usage examples:**

```bash
install_docker
install_make
verify_tools
```

---

## Project Layout (key bits)

* **API base path**: `/api/v2`
* **Services** (from `docker-compose.yml`):

  * `postgres` (DB)
  * `api` (Flask → Gunicorn)
* **Network**: `flask-net`
* **Volumes**:

  * Persistent DB data: `postgres_vol:/var/lib/postgresql/data`
  * Migrations folder bind‑mount: `./migrations:/app/migrations`  ← you mentioned `vol: ./...` and this is already present.

> Tip: The API only starts after Postgres is healthy (healthcheck is already defined in compose).

---

## Environment Variables

There are two places to be aware of:

1. **`.env` (local/dev defaults)**

   * Example:

     ```env
     FLASK_ENV=development
     LOG_LEVEL=INFO
     DATABASE_URL=postgresql+psycopg://myuser:mypassword@db:5432/mydatabase
     ```
2. **`docker-compose.yml` (runtime for containers)**

   * Example inside `api` service:

     ```yaml
     environment:
       FLASK_ENV: "production"
       DATABASE_URL: postgresql+psycopg://User1:User1password@postgres:5432/postgres_db
       FLASK_APP: wsgi
     ```

> **Keep them consistent** for your environment; compose vars override inside containers. If your DB creds differ between `.env` and compose, the app will use the compose ones when running via Docker.

---

## Make Targets & Order of Execution

Below is the expected flow. If a target doesn’t exist in your `Makefile`, see the **Appendix** for ready‑to‑copy target definitions.

### 0) Build images

```bash
make docker-build
```

* Builds the API image (e.g., `jayesh898/flask-api:v1.0.1`). Run this **after** any code changes that affect the image.

### 1) Start stack

```bash
make up
```

* Brings up `postgres` and `api` in the background (`-d`). Waits for DB healthcheck; API should come up afterwards.

### 2) Create / refresh migrations (only when models change)

```bash
make migrate
```

* Generates a new migration from current models (e.g., `flask db migrate -m "..."`).
* Uses the bind‑mounted `./migrations` so files persist on your host.

### 3) Apply migrations (always after step 2 on a new DB)

```bash
make upgrade
```

* Applies the migration to the running Postgres (e.g., `flask db upgrade`).

### 4) (Optional) Seed / smoke test

```bash
make seed   # if provided
make ps     # docker compose ps -a
```

### 5) Observe logs

```bash
make logs
```

* Tails the API logs (JSON structured) and DB logs.

### 6) Stop / destroy

```bash
make down   # stop & remove containers (keeps DB volume)
make clean  # optional: prune images/volumes if defined
```

---

## Quick API Checks (curl)

Base URL: `http://localhost:5000/api/v2`

```bash
# Health
curl -i /api/v2/health
curl -i /api/v2/db/health

# Students
curl -i /api/v2/students

# Create user1 & user2
curl -i -X POST /api/v2/students -H "Content-Type: application/json" \
  -d '{"name":"user1","age":20,"grade":"A","email":"user1@example.com"}'
curl -i -X POST /api/v2/students -H "Content-Type: application/json" \
  -d '{"name":"user2","age":22,"grade":"B","email":"user2@example.com"}'

# Get / Update / Delete
curl -i /api/v2/students/1
curl -i -X PUT /api/v2/students/1 -H "Content-Type: application/json" -d '{"grade":"A+"}'
curl -i -X DELETE /api/v2/students/2
```

> If running from a different directory, prepend full host: `http://localhost:5000` to each path.

---

## Troubleshooting

* **`permission denied: docker`** → run `newgrp docker` or log out/in after `install_docker`.
* **API can’t connect to DB** → confirm `DATABASE_URL` in compose matches the `postgres` service creds.
* **Migrations not generating** → ensure the container sees code changes; re‑run `make docker-build` if needed.
* **Port 5000 in use** → stop whatever is using it: `sudo lsof -i :5000` then kill the PID, or change the published port in compose.

---

## Appendix – Suggested Makefile Targets

If any targets are missing, add this minimal `Makefile` snippet:

```makefile
DOCKER_COMPOSE = docker compose
SERVICE_API = api

.PHONY: docker-build up down logs ps shell db-shell migrate upgrade seed clean

docker-build:
	$(DOCKER_COMPOSE) build --no-cache $(SERVICE_API)

up:
	$(DOCKER_COMPOSE) up -d

logs:
	$(DOCKER_COMPOSE) logs -f --tail=200

ps:
	$(DOCKER_COMPOSE) ps -a

shell:
	$(DOCKER_COMPOSE) exec $(SERVICE_API) /bin/sh

db-shell:
	$(DOCKER_COMPOSE) exec postgres psql -U User1 -d postgres_db

# Generate migration from model changes (inside API container)
migrate:
	$(DOCKER_COMPOSE) exec $(SERVICE_API) flask db migrate -m "auto"

# Apply migrations
upgrade:
	$(DOCKER_COMPOSE) exec $(SERVICE_API) flask db upgrade

seed:
	$(DOCKER_COMPOSE) exec $(SERVICE_API) python -c 'print("add your seed script here")'

down:
	$(DOCKER_COMPOSE) down

clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans || true
	docker image prune -f || true
```

> **Note on volumes**: The `./migrations:/app/migrations` bind mount ensures migration files you generate inside the container are saved to your host repo (and can be committed to git). The named volume `postgres_vol` persists DB data across container restarts.

---

## Team Notes

* Keep migration scripts in git so everyone shares the exact DB history.
* When you edit `models.py`, run **`make migrate` → `make upgrade`** and commit the generated files.
* Prefer **`docker compose`** (v2) over legacy `docker-compose`.
* If you change environment variables in compose, **recreate** the `api` service: `make down && make up`.

Happy shipping! 🚀
