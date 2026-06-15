PYTHON   := .venv/bin/python
PIP      := .venv/bin/pip
PYTEST   := .venv/bin/pytest
CELERY   := .venv/bin/celery
RUFF     := .venv/bin/ruff

.PHONY: help setup install migrate run worker test lint format shell superuser clean

help:
	@echo "Backend targets:"
	@echo "  setup      — create venv, install deps, run migrations (first-time setup)"
	@echo "  install    — install Python dependencies into .venv"
	@echo "  migrate    — apply database migrations"
	@echo "  run        — start Django dev server on :8000"
	@echo "  worker     — start Celery worker (requires Redis)"
	@echo "  test       — run pytest test suite"
	@echo "  lint       — run ruff linter"
	@echo "  format     — run ruff formatter"
	@echo "  shell      — open Django shell"
	@echo "  superuser  — create a superuser account"
	@echo "  clean      — remove .venv, .pyc files, and db.sqlite3"

setup: install migrate
	@echo ""
	@echo "  Ready. Run 'make run' to start the backend."

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q

migrate:
	$(PYTHON) manage.py migrate --noinput

run:
	$(PYTHON) manage.py runserver

worker:
	$(CELERY) -A core worker -l info --concurrency 2

test:
	$(PYTEST) tests/ -v

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

shell:
	$(PYTHON) manage.py shell

superuser:
	$(PYTHON) manage.py createsuperuser

clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f db.sqlite3

.DEFAULT_GOAL := help
