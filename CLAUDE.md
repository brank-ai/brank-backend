# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brank Backend is a Flask API that measures brand visibility across 4 LLMs (ChatGPT, Gemini, Grok, Perplexity). The main endpoint `GET /metric?website=<brand_website>` runs a 4-step pipeline: generate user questions via ChatGPT, query all 4 LLMs in parallel, extract brands/citations from responses, and calculate per-LLM metrics (brandRank, mentionRate, citationsList, sentimentScore). Results are cached for 24 hours.

## Commands

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run development server (port 5001)
python app.py

# Run tests
uv run pytest -v                                    # all tests
uv run pytest tests/test_metrics_calculator.py       # single file
uv run pytest tests/test_api.py::test_name           # single test

# Code quality
uv run black .                                       # format
uv run isort .                                       # sort imports
uv run mypy .                                        # type check
uv run ruff check .                                  # lint

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1

# Docker
docker-compose up                                    # runs on port 8080
```

## Architecture

**Layered structure with strict separation:**

- `api/` — Flask routes and Pydantic request/response schemas. Routes must be thin: validate input, get dependencies, call service, return response. No business logic.
- `services/` — Business logic orchestration. `metric_service.py` is the main pipeline orchestrator. Must NOT import Flask objects.
- `llm_clients/` — LLM provider integrations behind an `LLMClient` protocol. Factory creates only clients with valid API keys. Each client has retry logic with exponential backoff.
- `extractors/` — Sentiment analysis and data extraction from LLM responses.
- `db/models.py` — SQLAlchemy 2.0 models (6 tables: brands, prompts, responses, metrics, time_profiling, brand_insight_requests).
- `db/repositories/` — Data access layer. All DB access must go through repositories.
- `utils/` — Logging, timing decorators, retry logic, text/URL utilities.
- `config.py` — Pydantic Settings loading from `.env`. Validates API keys at startup (min 2 valid keys required).
- `app.py` — Flask application factory (`create_app()`). Entry point.

## Key Conventions

- **Dependency injection**: All dependencies (db_session, llm_clients, logger) passed as function parameters. No global singletons for DB connections or HTTP clients.
- **Type hints required** on all public functions (enforced by mypy with strict settings).
- **Formatting**: Black (88 chars), isort (black profile), ruff for linting.
- **Partial failure**: If one LLM fails, return results for the others. Never fail the entire request for a single LLM timeout.
- **Every network call must have a timeout** (default 30s).

## Critical Workflow Rules

- **Schema changes** (`db/models.py`): Always create an Alembic migration. CI checks this via `check-migrations.yml`.
- **API changes** (`api/routes.py`): Always update `brank-backend.postman_collection.json`. CI checks this via `check-postman.yml`.
- **Before PR**: Run `uv run pytest -v && uv run black . && uv run isort . && uv run mypy .`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metric` | Main pipeline — compute/return brand metrics (query: `website`) |
| GET | `/metrics/landingPage` | Average mention rates for preset brands |
| POST | `/brand-insight-request` | Submit brand insight request (body: `brand_name`, `email`), sends Slack notification |
| GET | `/metric/prompts` | Paginated prompts for a brand (query: `brand_name`/`website`, `page`, `per_page`) |
| GET | `/health` | Health check |
