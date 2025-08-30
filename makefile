VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask
PYTEST := $(VENV)/bin/pytest

export PYTHONPATH := $(PWD)
export FLASK_APP := wsgi:app 
export FLASK_NEW ?= development

IMAGE := student_api:dev
CONTAINER := student_api_dev
MESSAGE ?= auto-migration

.PHONY: help venv install run test \
        db-init db-migrate db-upgrade db-downgrade db-reset db-nuke db-head \
        docker-build docker-run docker-logs docker-stop docker-clean

help:
	@echo "Common commands:"
	@echo "  make run            - run the API locally"
	@echo "  make test           - run pytest"
	@echo "  make db-init        - create migrations/ folder (first time only)"
	@echo "  make db-migrate     - generate a new migration from model changes"
	@echo "  make db-upgrade     - apply migrations to DB (upgrade to head)"
	@echo "  make db-downgrade   - rollback last migration (downgrade one step)"
	@echo "  make db-reset       - drop everything (downgrade to base) then upgrade"
	@echo "  make docker-build   - build Docker image ($(IMAGE))"
	@echo "  make docker-run     - run container on :5000 (reads .env if present)"
	@echo "  make docker-logs    - tail container logs"
	@echo "  make docker-stop    - stop and remove container"
	@echo "  make docker-clean   - remove container + image"

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: venv
	$(FLASK) run -p 5000

test: venv
	$(PYTEST) -vv

db-init: venv
	$(FLASK) db init

db-migrate: venv
	$(FLASK) db migrate -m "$(MESSAGE)"

db-upgrade: venv
	$(FLASK) db upgrade

db-downgrade: venv
	$(FLASK) db downgrade


db-reset: venv
	$(FLASK) db downgrade base || true
	$(FLASK) db upgrade


docker-build:
	docker build -t $(IMAGE) .

docker-run:
	- docker rm -f $(CONTAINER) 2>/dev/null || true
	docker run --name $(CONTAINER) --env-file .env -p 5000:5000 $(IMAGE)

docker-logs:
	docker logs -f $(CONTAINER)

docker-stop:
	- docker rm -f $(CONTAINER) 2>/dev/null || true

docker-clean: docker-stop
	- docker rmi $(IMAGE) 2>/dev/null || true
