
## 0) Install tools (Ubuntu/Debian)

Copy this block and run what you need.

```bash
set -e

install_docker() {
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
  sudo systemctl enable --now docker
  echo "Docker installed. Run: newgrp docker"
}

install_make() { sudo apt-get update -y && sudo apt-get install -y make; }
install_git()  { sudo apt-get update -y && sudo apt-get install -y git; }
install_curl() { sudo apt-get update -y && sudo apt-get install -y curl; }
install_jq()   { sudo apt-get update -y && sudo apt-get install -y jq; }

verify_tools() {
  docker --version
  docker compose version
  make --version | head -n1
  git --version
  curl --version | head -n1
}
```

**Run:**

```bash
install_docker && install_make && install_git && install_curl && install_jq
newgrp docker
verify_tools
```

---

## 1) Get the code

```bash
git clone https://github.com/jayeshjeh/DevOps-Bootcamp.git
cd DevOps-Bootcamp
cp .env .env.local  # optional backup for your tweaks
```

> API base path: `/api/v2`
> Compose exposes port `5000`

---

## 2) Run in order (Make targets)

**Read this once:** your Makefile defines these useful targets:

* `docker-build`
* `docker-start-db`
* `docker-migrate-generate` (create migration file)
* `docker-upgrade` (apply migrations)
* `docker-start-api`
* `docker-logs`, `docker-stop`, `docker-clean`

> Note: The `start-api` target currently points to `docker-migrate` (not defined). Use the steps below instead.

### Steps

1. **Build image**

```bash
make docker-build
```

2. **Start Postgres and wait until healthy**

```bash
make docker-start-db
```

3. **Generate migration** (only when models changed)

```bash
make docker-migrate-generate MESSAGE="init schema"
```

4. **Apply migrations**

```bash
make docker-upgrade
```

5. **Start API**

```bash
make docker-start-api
```

6. **Logs (follow)**

```bash
make docker-logs
```

7. **Stop / Clean**

```bash
make docker-stop      # stop containers
make docker-clean     # stop + remove volumes + images
```

---

## 3) Quick check (curl)

```bash
curl -i http://localhost:5000/api/v2/health
curl -i http://localhost:5000/api/v2/db/health
```

(Optional) create two sample students:

```bash
curl -i -X POST http://localhost:5000/api/v2/students -H 'Content-Type: application/json' \
  -d '{"name":"user1","age":20,"grade":"A","email":"user1@example.com"}'

curl -i -X POST http://localhost:5000/api/v2/students -H 'Content-Type: application/json' \
  -d '{"name":"user2","age":22,"grade":"B","email":"user2@example.com"}'
```

---

## 4) Notes

* **Volumes**: `.:/app/` (bind‑mount so migration files are saved to your repo).
* **Rebuild when needed**: after changing Dockerfile/deps, run `make docker-build` again.

