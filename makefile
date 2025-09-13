
REGISTRY ?= jayesh898
NAME     ?= flask-api
TAG      ?= v1.0.1
IMAGE    ?= $(REGISTRY)/$(NAME):$(TAG)

MESSAGE  ?= "enter message"

.PHONY: help docker-build docker-start-db docker-migrate-generate docker-migrate docker-start-api docker-logs docker-stop docker-clean start-api

help:
	@echo "Available commands:"
	@echo "  make docker-build            - Build the REST API image ($(IMAGE))"
	@echo "  make docker-start-db         - Start Postgres and wait until healthy"
	@echo "  make docker-migrate-generate - Autogenerate a migration with Alembic"
	@echo "  make docker-upgrade          - Apply DB migrations (idempotent)"
# 	@echo "  make docker-start-api        - Start the API container"
	@echo "  make start-api               - DB -> wait -> migrate -> API"
	@echo "  make docker-logs             - Tail logs"
	@echo "  make docker-stop             - Stop and remove containers"
	@echo "  make docker-clean            - Stop + remove volumes + images"

docker-build:
	IMAGE=$(IMAGE) docker compose build api

docker-start-db:
	docker compose up -d postgres
	@echo "Waiting for Postgres to become healthy..."
	@until [ "$$(docker inspect --format='{{.State.Health.Status}}' postgres_db)" = "healthy" ]; do \
		echo "Postgres not healthy yet, retrying..."; \
		sleep 2; \
	done
	@echo "Postgres is healthy."

docker-migrate-generate:
	IMAGE=$(IMAGE) docker compose run --rm --no-deps api flask --app wsgi db migrate -m $(MESSAGE)

docker-upgrade:
	IMAGE=$(IMAGE) docker compose run --rm --no-deps api flask --app wsgi db upgrade

# docker-start-api:
# 	IMAGE=$(IMAGE) docker compose up -d api

docker-logs:
	docker compose logs -f

docker-stop:
	docker compose down

docker-clean:
	docker compose down -v --rmi all

start-api: docker-start-db docker-upgrade 
	docker compose up -d nginx
	docker compose up -d --scale api=2
	@echo "API started at http://localhost:5000"