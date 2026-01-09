# Brank Backend

Backend API for Brank - helps brands understand how Large Language Models (LLMs) perceive and recommend them.

## Overview

Brank analyzes how 4 major LLMs (ChatGPT, Gemini, Grok, Perplexity) respond to user questions where a brand could be relevant. It provides metrics on:

- **Brand Rank**: Average position where brand appears in responses
- **Citation Rate**: Most-cited URLs by each LLM
- **Mention Rate**: Percentage of responses mentioning the brand
- **Sentiment Score**: Overall sentiment toward the brand (0-100)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd brank-backend

# Install dependencies with uv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file in the project root:

```bash
# LLM API Keys
CHATGPT_API_KEY=sk-...
GEMINI_API_KEY=...
GROK_API_KEY=...
PERPLEXITY_API_KEY=...

# Configuration
PROMPTS_N=10
DATABASE_URL=postgresql://user:pass@localhost:5432/brank

# Optional
LLM_TIMEOUT_SECONDS=30
MAX_RETRIES=3

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### Database Setup

```bash
# Run migrations
alembic upgrade head
```

### Running the Server

```bash
# Development
flask run

# Production
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## API Usage

### Get Brand Metrics

```bash
GET /metric?website=samsung.com
```

**Response** (200 OK):
```json
{
  "brand_id": "uuid",
  "website": "samsung.com",
  "cached": false,
  "computed_at": "2026-01-09T10:30:00Z",
  "metrics": {
    "chatgpt": {
      "brandRank": 1.75,
      "citationsList": [
        {"url": "https://samsung.com/...", "percentage": 80.0},
        {"url": "https://gsmarena.com/...", "percentage": 60.0}
      ],
      "mentionRate": 0.8,
      "sentimentScore": 75.5
    },
    "gemini": { /* ... */ },
    "grok": { /* ... */ },
    "perplexity": { /* ... */ }
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "website parameter required"
}
```

## Project Structure

```
brank-backend/
├── api/              # Flask routes, request/response handling
├── services/         # Business logic orchestration
├── llm_clients/      # LLM provider integrations
├── extractors/       # Brand/URL extraction, sentiment analysis
├── db/               # Database models, repositories, migrations
├── utils/            # Logging, timing, retry utilities
├── tests/            # Unit and integration tests
├── docs/             # Documentation
├── .cursorrules      # Cursor AI agent rules
├── .cursorignore     # Files to ignore
├── pyproject.toml    # Project configuration
└── README.md         # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=brank_backend --cov-report=html

# Run specific test file
pytest tests/test_metrics.py
```

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Run linter
ruff check .
```

### Type Checking

```bash
mypy brank_backend/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design, database schema, and metric calculation algorithms.

### Key Features

- **24-hour caching**: Metrics cached for 24h to avoid redundant LLM queries
- **Parallel LLM queries**: All 4 LLMs queried simultaneously for speed
- **Partial failure handling**: Returns results even if some LLMs fail
- **Performance tracking**: Logs timing for each pipeline step
- **Dependency injection**: Clean architecture preventing memory leaks

## Cursor AI Development

This repository is optimized for development with [Cursor](https://cursor.sh/) in agentic mode. The `.cursorrules` file provides comprehensive context about:

- Project architecture and layering
- Database schema and relationships
- Metric calculation algorithms
- Code standards and patterns
- Security best practices

When developing with Cursor's AI agent, it will automatically follow these rules to maintain consistency and quality.

## Environment Variables Reference

| Variable                     | Required | Default | Description                        |
|------------------------------|----------|---------|------------------------------------|
| `CHATGPT_API_KEY`            | Yes      | -       | OpenAI API key                     |
| `GEMINI_API_KEY`             | Yes      | -       | Google Gemini API key              |
| `GROK_API_KEY`               | Yes      | -       | xAI Grok API key                   |
| `PERPLEXITY_API_KEY`         | Yes      | -       | Perplexity API key                 |
| `PROMPTS_N`                  | No       | 10      | Number of prompts to generate      |
| `DATABASE_URL`               | Yes      | -       | PostgreSQL connection string       |
| `LLM_TIMEOUT_SECONDS`        | No       | 30      | Timeout for LLM API calls          |
| `MAX_RETRIES`                | No       | 3       | Max retry attempts for failed calls|
| `FLASK_ENV`                  | No       | dev     | Flask environment                  |
| `SECRET_KEY`                 | Yes      | -       | Flask secret key                   |

## Performance

### Expected Response Times

- **Cached request**: ~50ms
- **Fresh computation**: ~15-30 seconds
  - Prompt generation: ~2-5s
  - LLM queries (parallel): ~10-20s
  - Processing + metrics: ~2-3s

### Optimization

- Uses parallel LLM queries to minimize latency
- Connection pooling for database and HTTP
- Indexed database queries for fast lookups
- 24h cache significantly reduces LLM API costs

## Troubleshooting

### Common Issues

**"API key not found"**
- Ensure `.env` file exists and contains all required API keys
- Check that python-dotenv is installed

**"Database connection failed"**
- Verify PostgreSQL is running
- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Ensure database exists and migrations are applied

**"LLM timeout"**
- Increase `LLM_TIMEOUT_SECONDS` if network is slow
- Check API key validity
- Verify provider API status

## Contributing

1. Follow the coding standards defined in `.cursorrules`
2. Write tests for new features
3. Run formatters and linters before committing
4. Update documentation as needed

## License

[Your License Here]

## Support

For issues and questions, please [open an issue](link-to-issues).

---

**Built with Python, Flask, and love for clean architecture** ❤️

