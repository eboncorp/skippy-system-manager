# Skippy System Manager - Makefile
# Common development and operations tasks

.PHONY: help setup dev-setup test lint format clean install

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

#==============================================================================
# Help
#==============================================================================

help: ## Show this help message
	@echo "$(BLUE)Skippy System Manager - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make setup          # Initial setup"
	@echo "  make test           # Run tests"
	@echo "  make lint           # Check code quality"

#==============================================================================
# Setup and Installation
#==============================================================================

setup: ## Initial project setup (install deps, create config)
	@echo "$(BLUE)Setting up Skippy System Manager...$(NC)"
	@echo "$(GREEN)Installing system dependencies...$(NC)"
	sudo apt-get update || true
	sudo apt-get install -y python3 python3-pip jq curl gpg shellcheck || true
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)Creating configuration file...$(NC)"
	[ -f config.env ] || cp config.env.example config.env
	@echo "$(YELLOW)Please edit config.env with your settings$(NC)"
	@echo "$(GREEN)Setup complete!$(NC)"

dev-setup: setup ## Setup development environment (includes test deps)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	pip install -r requirements-test.txt
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)Development environment ready!$(NC)"

install: ## Install Skippy as a package
	pip install -e .

validate-config: ## Validate configuration
	@echo "$(BLUE)Validating configuration...$(NC)"
	@bash -c 'source config.env && bash scripts/utility/validate_config.sh'

#==============================================================================
# Testing
#==============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration

test-security: ## Run security tests
	@echo "$(BLUE)Running security tests...$(NC)"
	pytest -m security

test-wordpress: ## Run WordPress tests
	@echo "$(BLUE)Running WordPress tests...$(NC)"
	pytest -m wordpress

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov --cov-report=term-missing

coverage-html: ## Generate HTML coverage report
	@echo "$(BLUE)Generating HTML coverage report...$(NC)"
	pytest --cov --cov-report=html
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest --watch

#==============================================================================
# Code Quality
#==============================================================================

lint: lint-python lint-shell ## Run all linters

lint-python: ## Lint Python code
	@echo "$(BLUE)Linting Python code...$(NC)"
	-pylint lib/python/ mcp-servers/
	-flake8 lib/python/ mcp-servers/
	-mypy lib/python/ mcp-servers/

lint-shell: ## Lint shell scripts
	@echo "$(BLUE)Linting shell scripts...$(NC)"
	-find scripts/ -name "*.sh" -not -path "*/archive/*" -not -path "*/legacy_system_managers/*" | xargs shellcheck

format: format-python ## Format code automatically

format-python: ## Format Python code with black
	@echo "$(BLUE)Formatting Python code...$(NC)"
	black lib/python/ mcp-servers/ tests/
	isort lib/python/ mcp-servers/ tests/

format-check: ## Check if code is formatted correctly
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check lib/python/ mcp-servers/ tests/
	isort --check lib/python/ mcp-servers/ tests/

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r lib/python/ -ll
	-detect-secrets scan

type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy lib/python/ mcp-servers/

#==============================================================================
# Documentation
#==============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)Documentation server not yet implemented$(NC)"

#==============================================================================
# Scripts
#==============================================================================

list-scripts: ## List all active scripts
	@echo "$(BLUE)Active Scripts:$(NC)"
	@find scripts/ -type f \( -name "*.sh" -o -name "*.py" \) \
		-not -path "*/archive/*" \
		-not -path "*/legacy_system_managers/*" \
		| sort

list-deprecated: ## List deprecated scripts
	@echo "$(BLUE)Deprecated Scripts:$(NC)"
	@find scripts/archive/ scripts/legacy_system_managers/ -type f \( -name "*.sh" -o -name "*.py" \) | sort

consolidate-scripts: ## Run script consolidation tool
	@echo "$(BLUE)Consolidating scripts...$(NC)"
	bash scripts/maintenance/consolidate_legacy_v1.0.0.sh

#==============================================================================
# MCP Server
#==============================================================================

mcp-start: ## Start MCP server
	@echo "$(BLUE)Starting MCP server...$(NC)"
	cd mcp-servers/general-server && python server.py

mcp-test: ## Test MCP server
	@echo "$(BLUE)Testing MCP server...$(NC)"
	pytest tests/unit/test_mcp_server_config.py

#==============================================================================
# Git Operations
#==============================================================================

git-check: ## Check git status and uncommitted changes
	@echo "$(BLUE)Git Status:$(NC)"
	@git status --short
	@echo ""
	@echo "$(BLUE)Uncommitted Changes:$(NC)"
	@git diff --stat

pre-commit: lint test ## Run pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed!$(NC)"

#==============================================================================
# Cleanup
#==============================================================================

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: clean ## Clean everything including config
	rm -f config.env
	@echo "$(YELLOW)Remember to create new config.env$(NC)"

#==============================================================================
# WordPress Operations
#==============================================================================

wp-backup: ## Run WordPress backup
	@echo "$(BLUE)Running WordPress backup...$(NC)"
	bash scripts/backup/full_home_backup_v1.0.0.sh

wp-update: ## Update WordPress (core, plugins, themes)
	@echo "$(BLUE)Updating WordPress...$(NC)"
	@echo "$(YELLOW)Not yet implemented - use MCP server$(NC)"

#==============================================================================
# Monitoring
#==============================================================================

status: ## Show system status dashboard
	@echo "$(BLUE)System Status:$(NC)"
	bash scripts/monitoring/system_dashboard_v1.0.0.sh snapshot

monitor: ## Start system monitoring
	@echo "$(BLUE)Starting system monitoring...$(NC)"
	bash scripts/monitoring/system_dashboard_v1.0.0.sh monitor

#==============================================================================
# Docker Operations
#==============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker-compose build

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## Show Docker logs
	@echo "$(BLUE)Docker logs:$(NC)"
	docker-compose logs -f

docker-shell: ## Open shell in Docker container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	docker-compose exec skippy-mcp /bin/bash

#==============================================================================
# CI/CD
#==============================================================================

ci: lint test ## Run CI checks locally
	@echo "$(GREEN)CI checks passed!$(NC)"

ci-full: lint test security-check ## Run full CI pipeline locally
	@echo "$(GREEN)Full CI checks passed!$(NC)"

#==============================================================================
# Release
#==============================================================================

changelog: ## Generate changelog
	@echo "$(BLUE)Generating changelog...$(NC)"
	@git log --oneline --decorate --graph > CHANGELOG.txt
	@echo "$(GREEN)Changelog generated: CHANGELOG.txt$(NC)"

version: ## Show current version
	@echo "$(BLUE)Skippy System Manager$(NC)"
	@echo "Version: $$(git describe --tags --always 2>/dev/null || echo 'dev')"
	@echo "Commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
	@echo "Branch: $$(git branch --show-current 2>/dev/null || echo 'unknown')"

#==============================================================================
# Maintenance
#==============================================================================

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-test.txt

migrate-ssh-keys: ## Migrate to SSH key authentication
	@echo "$(BLUE)Migrating to SSH keys...$(NC)"
	bash scripts/security/migrate_to_ssh_keys_v1.0.0.sh

backup-encrypt: ## Add encryption to backups
	@echo "$(BLUE)Encrypting backups...$(NC)"
	@echo "$(YELLOW)Not yet implemented$(NC)"

#==============================================================================
# Development Helpers
#==============================================================================

shell: ## Start Python shell with context
	@echo "$(BLUE)Starting Python shell...$(NC)"
	python -i -c "import sys; sys.path.insert(0, 'lib/python'); from skippy_logger import get_logger; from skippy_validator import validate_path; logger = get_logger('shell'); print('Skippy shell ready! Available: logger, validate_path')"

watch-logs: ## Watch Skippy logs
	@echo "$(BLUE)Watching logs...$(NC)"
	tail -f logs/skippy_combined.log || echo "$(YELLOW)No logs found yet$(NC)"

info: ## Show project information
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(BLUE)  Skippy System Manager$(NC)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(GREEN)Version:$(NC)     $$(git describe --tags --always 2>/dev/null || echo 'dev')"
	@echo "$(GREEN)Branch:$(NC)      $$(git branch --show-current 2>/dev/null || echo 'unknown')"
	@echo "$(GREEN)Commit:$(NC)      $$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
	@echo "$(GREEN)Python:$(NC)      $$(python3 --version 2>/dev/null || echo 'not found')"
	@echo "$(GREEN)Scripts:$(NC)     $$(find scripts/ -type f \( -name '*.sh' -o -name '*.py' \) ! -path '*/archive/*' ! -path '*/legacy_system_managers/*' | wc -l)"
	@echo "$(GREEN)Tests:$(NC)       $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo ""
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

#==============================================================================
# Shortcuts
#==============================================================================

t: test ## Shortcut for 'make test'
l: lint ## Shortcut for 'make lint'
f: format ## Shortcut for 'make format'
c: clean ## Shortcut for 'make clean'
s: status ## Shortcut for 'make status'
i: info ## Shortcut for 'make info'
