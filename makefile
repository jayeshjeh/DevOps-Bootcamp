
DOCKERHUB_USER ?= jayesh898
NAME     ?= flask-api
TAG      ?= v2.0.1
IMAGE    ?= $(DOCKERHUB_USER)/$(NAME):$(TAG)

.PHONY: dependency, lint, test, docker-login, docker-build, docker-push

help:
	@echo "Available commands:"
	@echo "  make docker-build            - Build the REST API image ($(IMAGE))"
	@echo "  make dependency              - Install dependency "
	@echo "  make lint    				  - Lint with Pylint"
	@echo "  make test                    - Run pytest"
	@echo "  make docker login            - Login to dockerhub"
	@echo "  make docker-buiild           - docker build "
	@echo "  make docker push             - docekr image push"

dependency:
	python3 -m pip install -r requirements.txt

lint: dependency
	pylint -E app

test: dependency
	PYTHONPATH=. pytest -q

docker-login:
	@echo "$$TOKEN" | docker login -u $(DOCKERHUB_USER) --password-stdin

docker-build:
	docker build -t $(IMAGE) .

docker-push:
	docker push $(IMAGE)

