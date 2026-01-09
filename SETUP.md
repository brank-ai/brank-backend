# Setup Guide for brank-backend

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 13 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- API keys for: OpenAI (ChatGPT), Google (Gemini), xAI (Grok), Perplexity

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
cd /path/to/brank-backend
```

### 2. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install uv
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev tools
uv pip install -e ".[dev]"

# Verify installation
python -c "import flask; import sqlalchemy; import openai; print('✓ Dependencies installed')"
```

### 4. Set Up PostgreSQL Database

```bash
# Create database
createdb brank

# Verify
psql -l | grep brank
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from example (you'll need to create .env manually as .env.example was blocked)
cat > .env << 'EOF'
# LLM API Keys (REQUIRED - get from providers)
CHATGPT_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-google-gemini-api-key-here
GROK_API_KEY=your-xai-grok-api-key-here
PERPLEXITY_API_KEY=your-perplexity-api-key-here

# Pipeline Configuration
PROMPTS_N=10

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@localhost:5432/brank

# Timeouts and Retries
LLM_TIMEOUT_SECONDS=30
MAX_RETRIES=3
RETRY_MIN_WAIT=2
RETRY_MAX_WAIT=10

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True

# Logging
LOG_LEVEL=INFO
EOF
```

**Important**: Edit the `.env` file and add your actual API keys!

### 6. Run Database Migrations

```bash
# Apply all migrations to create tables
alembic upgrade head

# Verify tables were created
psql brank -c "\dt"
```

Expected tables:
- `brands`
- `prompts`
- `responses`
- `metrics`
- `time_profiling`
- `alembic_version`

### 7. Run Tests (Optional but Recommended)

```bash
# Run unit tests
pytest tests/test_metrics_calculator.py tests/test_extractors.py -v

# Run all tests
pytest -v
```

### 8. Start the Server

```bash
# Option 1: Using Python directly
python app.py

# Option 2: Using Flask CLI
flask run --debug

# Option 3: With custom host/port
flask run --host=0.0.0.0 --port=5000
```

Server will start at `http://localhost:5000`

### 9. Test the API

```bash
# Health check
curl http://localhost:5000/health

# Expected: {"status": "healthy"}

# Test /metric endpoint
curl "http://localhost:5000/metric?website=samsung.com"

# This will take 15-30 seconds for the first request
# Subsequent requests within 24h will be instant (cached)
```

---

## Getting API Keys

### OpenAI (ChatGPT)

1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy key (starts with `sk-`)
5. Add to `.env` as `CHATGPT_API_KEY=sk-...`

### Google (Gemini)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API key"
4. Copy key
5. Add to `.env` as `GEMINI_API_KEY=...`

### xAI (Grok)

1. Go to https://x.ai/api
2. Sign in
3. Get API key from dashboard
4. Add to `.env` as `GROK_API_KEY=...`

### Perplexity

1. Go to https://www.perplexity.ai/settings/api
2. Sign in
3. Generate API key
4. Add to `.env` as `PERPLEXITY_API_KEY=...`

---

## Troubleshooting

### "Module not found" errors

```bash
# Reinstall dependencies
uv pip install -e ".[dev]" --force-reinstall
```

### Database connection failed

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### API key errors

```bash
# Verify keys are loaded
python -c "from config import get_settings; s = get_settings(); print('Keys loaded')"

# Check .env file exists
ls -la .env
```

### Alembic migration errors

```bash
# Reset alembic
alembic downgrade base
alembic upgrade head

# If that fails, drop and recreate database
dropdb brank
createdb brank
alembic upgrade head
```

---

## Development Tips

### Running in Development Mode

```bash
# Auto-reload on code changes
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Viewing Logs

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
python app.py
```

### Using a Different Database

```bash
# SQLite (for quick testing, not recommended for production)
export DATABASE_URL="sqlite:///brank.db"

# Remote PostgreSQL
export DATABASE_URL="postgresql://user:pass@remote-host:5432/brank"
```

### Testing with Fewer Prompts (Faster)

```bash
# Generate only 3 prompts instead of 10
export PROMPTS_N=3
python app.py
```

---

## Next Steps

1. ✅ Setup complete
2. ✅ Server running
3. ✅ API responding

See `TESTING.md` for comprehensive testing guide.
See `README.md` for usage examples and API documentation.
See `docs/ARCHITECTURE.md` for system design details.

---

## Quick Reference Commands

```bash
# Start server
python app.py

# Run tests
pytest -v

# Run migrations
alembic upgrade head

# Check database
psql brank -c "SELECT * FROM brands;"

# View logs
tail -f logs/app.log  # if logging to file

# Format code
black .
isort .

# Type check
mypy .
```

Happy coding! 🚀

