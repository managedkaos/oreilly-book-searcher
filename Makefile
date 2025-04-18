APP = $(notdir $(CURDIR))
TAG = $(shell echo "$$(date +%F)-$$(git rev-parse --short HEAD)")
DOCKER_REPO = ghcr.io/managedkaos


help:
	@echo "Run make <target> where target is one of the following..."
	@echo
	@echo "  all                      - run requirements, lint, test, and build"
	@echo "  requirements             - install runtime dependencies"
	@echo "  development-requirements - install development dependencies"
	@echo "  lint                     - run flake8, pylint, black, and isort checks"
	@echo "  black                    - format code with black"
	@echo "  isort                    - sort imports with isort"
	@echo "  test                     - run unit tests"
	@echo "  build                    - build docker container"
	@echo "  clean                    - clean up workspace and containers"

all: requirements lint test build

development-requirements: requirements
	pip install --quiet --upgrade --requirement development-requirements.txt

requirements:
	pip install --upgrade pip
	pip install --quiet --upgrade --requirement requirements.txt

lint:
	flake8 --ignore=E501,E231 *.py
	pylint --errors-only --disable=C0301 *.py
	black --diff *.py
	isort --check-only --diff *.py

fmt: black isort

black:
	black *.py

isort:
	isort *.py

test:
	pytest test_main.py -v

local:
	python main.py

build: lint test
	docker build --tag $(APP):$(TAG) .

run:
	docker run -it --rm \
	  --volume $(PWD)/titles.txt:/work/titles.txt:ro \
	  --volume $(PWD)/data:/work/data \
	  $(APP):$(TAG) \

clean:
	docker container stop $(APP) || true
	docker container rm $(APP) || true
	@rm -rf ./__pycache__ ./tests/__pycache__
	@rm -f .*~ *.pyc

nuke: clean
	/bin/rm -rvf ./data

.PHONY: help requirements lint black isort test build clean development-requirements
