.PHONY: setup run clean clean-logs test test-unit test-service test-specific lint db-init db-seed db-reset db-migrate db-status help

.DEFAULT_GOAL := help

PYTHON = python3.11
VENV = venv311
VENV_BIN = $(VENV)/bin
VENV_PYTHON = $(VENV_BIN)/python
DB_MANAGE = $(PYTHON) db_manage.py

help:
	@echo "Mathtermind Makefile"
	@echo "===================="
	@echo "Available commands:"
	@echo "  make setup      - Set up the project (create venv, install dependencies, init db)"
	@echo "  make run        - Run the application"
	@echo "  make clean      - Clean up temporary files and caches"
	@echo "  make clean-logs - Clean up error logs in logs/error_reports directory"
	@echo "  make test       - Run all tests"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-service SERVICE=<service_name> - Run tests for specific service (e.g., cs_tools)"
	@echo "  make test-specific PATH=<path> - Run specific test file or directory"
	@echo "  make lint       - Run linting tools"
	@echo "  make db-init    - Initialize the database"
	@echo "  make db-seed    - Seed the database with sample data"
	@echo "  make db-reset   - Reset the database"
	@echo "  make db-migrate - Run database migrations"
	@echo "  make db-status  - Show database migration status"

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install -r requirements.txt

run:
	PYTHONPATH=$(shell pwd) $(shell pwd)/$(VENV_PYTHON) -m src.ui.main

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/*/__pycache__
	rm -rf src/*/*/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -name "*.pyc" -delete

clean-logs:
	find logs/error_reports -name "*.json" -type f -delete
	@echo "Error logs cleaned successfully"

test:
	$(PYTHON) -m pytest

test-unit:
	$(PYTHON) -m pytest -m unit

test-service:
	$(PYTHON) -m pytest src/tests/services/test_$(SERVICE)_service.py -v

test-specific:
	$(PYTHON) -m pytest $(PATH) -v

lint:
	$(PYTHON) -m flake8 src
	$(PYTHON) -m black --check src

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing --cov-report=html

db-init:
	$(VENV_PYTHON) db_manage.py init

db-seed:
	$(VENV_PYTHON) db_manage.py seed

db-reset:
	$(VENV_PYTHON) db_manage.py reset

db-migrate:
	$(VENV_PYTHON) db_manage.py migrate

db-status:
	$(VENV_PYTHON) db_manage.py status 
