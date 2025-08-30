# Student REST API

A simple REST API built with **Flask**, **PostgreSQL**, and **SQLAlchemy** to manage student records. The project demonstrates production-ready practices such as API versioning, configuration via environment variables, structured logging, health checks, unit testing, and database migrations.

---

## Features

* **CRUD Endpoints**

  * Add a new student
  * Get all students
  * Get a student by ID
  * Update existing student information
  * Delete a student record

* **Best Practices**

  * Config managed via environment variables (`.env`)
  * API versioning (e.g., `/api/v2/...`)
  * Structured JSON logging
  * `/health` and `/db/health` endpoints
  * Unit tests with pytest
  * Database migrations with Flask-Migrate
  * Dependencies tracked in `requirements.txt`
  * Docker support

---

## Project Structure

```
app/
 ├── __init__.py        # App factory, logging, config load
 ├── config.py          # Config classes (Dev, Prod, Test)
 ├── models.py          # SQLAlchemy models
 ├── routes.py          # API routes
 ├── extensions.py      # db and migrate instances
 └── wsgi.py            # Entrypoint for Gunicorn/Docker

migrations/             # Created after db init
requirements.txt        # Dependencies
Makefile                # Helper commands
tests/                  # Pytest tests
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/student-api.git
cd student-api
```

### 2. Create virtual environment and install dependencies

```bash
make venv
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase
API_VERSION=v2
LOG_LEVEL=INFO
OWNER=yourname
BUILD=local
```

### 4. Run database migrations

```bash
make db-init      # only the first time
make db-migrate MESSAGE="create students"
make db-upgrade
```

### 5. Run the API locally

```bash
make run
```

Check:

* [http://localhost:5000/api/v2/health](http://localhost:5000/api/v2/health)
* [http://localhost:5000/api/v2/students](http://localhost:5000/api/v2/students)

### 6. Run tests

```bash
make test
```

---

## Docker Setup

### Build the image

```bash
make docker-build
```

### Run the container

```bash
make docker-run
```

API will be available at:

* [http://localhost:5000/api/v2/health](http://localhost:5000/api/v2/health)

### Stop and clean up

```bash
make docker-stop
make docker-clean
```

---

## Makefile Commands

* `make run` → run API locally
* `make test` → run tests
* `make db-migrate MESSAGE="..."` → create migration
* `make db-upgrade` → apply migrations
* `make db-reset` → drop & reapply schema
* `make docker-build` → build Docker image
* `make docker-run` → run Docker container

---

## Health Endpoints

* `GET /api/v2/health` → API health info
* `GET /api/v2/db/health` → DB connectivity check

---

## License

MIT License
