.PHONY: help install dev test test-fast test-cov lint format check clean docker-build docker-run docker-stop docker-logs docker-shell docker-dev docker-down docker-clean

# Default target
help:
	@echo "Pocket Portals - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install dependencies with uv"
	@echo ""
	@echo "Development:"
	@echo "  make dev         Start FastAPI server (port 8888)"
	@echo "  make dev-reload  Start server with auto-reload"
	@echo ""
	@echo "Testing (TDD):"
	@echo "  make test        Run all tests with coverage"
	@echo "  make test-fast   Run tests, stop on first failure"
	@echo "  make test-cov    Run tests with HTML coverage report"
	@echo "  make test-watch  Run tests in watch mode"
	@echo ""
	@echo "Quality:"
	@echo "  make lint        Check code style (ruff)"
	@echo "  make format      Auto-fix code style"
	@echo "  make check       Run all quality gates"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-run      Run container (detached)"
	@echo "  make docker-stop     Stop container"
	@echo "  make docker-logs     View container logs"
	@echo "  make docker-shell    Open shell in running container"
	@echo "  make docker-dev      Run with docker-compose (hot reload)"
	@echo "  make docker-down     Stop docker-compose services"
	@echo "  make docker-clean    Remove images and containers"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       Remove build artifacts"

# ============================================================
# Setup
# ============================================================

install:
	uv pip install -e ".[dev]"
	uv run pre-commit install
	@echo "✅ Dependencies installed"

# ============================================================
# Development
# ============================================================

dev:
	uv run uvicorn src.api.main:app --port 8888

dev-reload:
	uv run uvicorn src.api.main:app --reload --port 8888

# ============================================================
# Testing (TDD Workflow)
# ============================================================

# Full test suite with coverage
test:
	uv run pytest --cov=src --cov-report=term-missing -v

# Stop on first failure (for TDD red/green cycle)
test-fast:
	uv run pytest -x -v

# Generate HTML coverage report
test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report: open htmlcov/index.html"

# Watch mode (requires pytest-watch)
test-watch:
	uv run ptw -- -x -v

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=tests/test_api.py"
	uv run pytest $(FILE) -v

# ============================================================
# Quality Gates
# ============================================================

# Check lint without fixing
lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	@echo "✅ Lint passed"

# Auto-fix lint issues
format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/
	@echo "✅ Code formatted"

# Run all quality gates (pre-commit check)
check: lint test
	@echo ""
	@echo "✅ All quality gates passed!"

# ============================================================
# Git Workflow
# ============================================================

# Pre-commit check (same as check)
pre-commit: check

# Status check
status:
	@git status
	@echo ""
	@git log --oneline -5

# ============================================================
# Docker
# ============================================================

# Docker configuration
IMAGE_NAME = pocket-portals
CONTAINER_NAME = pocket-portals-app
DOCKER_PORT = 8888

# Build Docker image
docker-build:
	docker build -t $(IMAGE_NAME):latest .
	@echo "✅ Docker image built: $(IMAGE_NAME):latest"

# Run container (detached)
docker-run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(DOCKER_PORT):8888 \
		$(IMAGE_NAME):latest
	@echo "✅ Container running: http://localhost:$(DOCKER_PORT)"
	@echo "   Use 'make docker-logs' to view logs"

# Stop container
docker-stop:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "✅ Container stopped and removed"

# View container logs
docker-logs:
	docker logs -f $(CONTAINER_NAME)

# Open shell in running container
docker-shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Run with docker-compose for development (hot reload)
docker-dev:
	docker-compose up --build
	@echo "✅ Development environment started"

# Stop docker-compose services
docker-down:
	docker-compose down
	@echo "✅ Docker Compose services stopped"

# Remove images and containers
docker-clean:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME):latest 2>/dev/null || true
	docker-compose down -v --remove-orphans 2>/dev/null || true
	@echo "✅ Docker images and containers removed"

# ============================================================
# Cleanup
# ============================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned build artifacts"

# ============================================================
# Quick Reference (TDD Cycle)
# ============================================================
#
# 1. RED:    Write failing test
#            make test-fast  (should fail)
#
# 2. GREEN:  Write minimal code to pass
#            make test-fast  (should pass)
#
# 3. REFACTOR: Clean up code
#            make test       (should still pass)
#
# 4. COMMIT:
#            make check      (quality gates)
#            git add . && git commit
#
# ============================================================
