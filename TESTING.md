# Testing Guide for brank-backend

## Setup

### 1. Install Dependencies

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"
```

### 2. Set Up PostgreSQL Database

```bash
# Create test database
createdb brank_test

# Set environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/brank_test"
```

### 3. Configure Environment Variables

Create a `.env` file for testing:

```bash
# LLM API Keys (use real keys for integration testing)
CHATGPT_API_KEY=sk-your-test-key
GEMINI_API_KEY=your-test-key
GROK_API_KEY=your-test-key
PERPLEXITY_API_KEY=your-test-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/brank_test

# Configuration (use smaller values for testing)
PROMPTS_N=3
LLM_TIMEOUT_SECONDS=30
MAX_RETRIES=2

# Flask
FLASK_ENV=development
SECRET_KEY=test-secret-key
DEBUG=True
LOG_LEVEL=DEBUG
```

---

## Running Tests

### Unit Tests Only

```bash
# Run all unit tests
pytest tests/test_metrics_calculator.py tests/test_extractors.py -v

# Run with coverage
pytest tests/test_metrics_calculator.py tests/test_extractors.py --cov=services --cov=extractors
```

### Integration Tests

```bash
# Run API integration tests (mocked)
pytest tests/test_api.py -v
```

### All Tests

```bash
# Run entire test suite
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
```

---

## Manual Testing

### Step 1: Apply Database Migrations

```bash
# Run migrations to create tables
alembic upgrade head
```

### Step 2: Start the Server

```bash
# Start Flask development server
python app.py

# Or use Flask CLI
flask run --debug
```

Server will start on `http://localhost:5000`

### Step 3: Test Health Endpoint

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

### Step 4: Test /metric Endpoint (Fresh Computation)

```bash
# Test with a real brand
curl "http://localhost:5000/metric?website=samsung.com"
```

**Expected Response** (takes 15-30 seconds):
```json
{
  "brand_id": "uuid-here",
  "website": "samsung.com",
  "cached": false,
  "computed_at": "2026-01-09T12:30:00Z",
  "metrics": {
    "chatgpt": {
      "brandRank": 1.5,
      "citationsList": [
        {"url": "https://samsung.com", "percentage": 80.0},
        {"url": "https://gsmarena.com", "percentage": 60.0}
      ],
      "mentionRate": 0.8,
      "sentimentScore": 75.5
    },
    "gemini": {
      "brandRank": 2.0,
      "citationsList": [...],
      "mentionRate": 0.7,
      "sentimentScore": 72.0
    },
    "grok": {
      "brandRank": 1.8,
      "citationsList": [...],
      "mentionRate": 0.75,
      "sentimentScore": 73.0
    },
    "perplexity": {
      "brandRank": 1.6,
      "citationsList": [...],
      "mentionRate": 0.85,
      "sentimentScore": 78.0
    }
  }
}
```

### Step 5: Test Cache (Call Same Endpoint Within 24h)

```bash
# Call same endpoint again immediately
curl "http://localhost:5000/metric?website=samsung.com"
```

**Expected**: Same response but with `"cached": true` and instant response time (~50ms)

### Step 6: Test Error Handling

```bash
# Missing website parameter
curl "http://localhost:5000/metric"
```

Expected: `400 Bad Request`

```bash
# Invalid website format
curl "http://localhost:5000/metric?website=not-a-valid-url"
```

Expected: May still work (creates brand) or returns error depending on validation

---

## Verification Checklist

After manual testing, verify the following:

### ✅ Database Records

```sql
-- Check brands table
SELECT * FROM brands WHERE website = 'samsung.com';

-- Check prompts generated
SELECT COUNT(*) FROM prompts WHERE brand_id = '<brand_id_from_above>';
-- Should equal PROMPTS_N (e.g., 10)

-- Check responses (should be prompts_n × 4 LLMs)
SELECT llm_name, COUNT(*) FROM responses r
JOIN prompts p ON r.prompt_id = p.prompt_id
WHERE p.brand_id = '<brand_id>'
GROUP BY llm_name;
-- Each LLM should have ~10 responses

-- Check metrics (should be 4 rows, one per LLM)
SELECT llm_name, brand_rank, mention_rate, sentiment_score 
FROM metrics 
WHERE brand_id = '<brand_id>';

-- Check timing profile
SELECT * FROM time_profiling WHERE brand_id = '<brand_id>';
```

### ✅ Metrics Validation

1. **brandRank**: Should be between 1.0 and ~10.0 (or null if brand never appears)
2. **citationsList**: Array of up to 5 URLs with percentages 0-100
3. **mentionRate**: Float between 0.0 and 1.0
4. **sentimentScore**: Float between 0.0 and 100.0

### ✅ Performance Validation

Check `time_profiling` table:

```sql
SELECT 
  prompt_generation_time,
  fetching_llm_response_time,
  processing_response_time,
  metrics_calculation_time,
  (prompt_generation_time + fetching_llm_response_time + 
   processing_response_time + metrics_calculation_time) as total_time
FROM time_profiling
ORDER BY created_at DESC
LIMIT 1;
```

Expected times:
- `prompt_generation_time`: ~2-5 seconds
- `fetching_llm_response_time`: ~10-20 seconds (parallel queries)
- `processing_response_time`: ~1-2 seconds
- `metrics_calculation_time`: ~1 second
- **Total**: ~15-30 seconds

### ✅ Cache Validation

1. First request: `"cached": false`, takes ~15-30s
2. Second request (within 24h): `"cached": true`, takes ~50ms
3. Check `updated_at` in metrics table is recent

---

## Testing Different Brands

Test with various brands to ensure robustness:

```bash
# Technology brands
curl "http://localhost:5000/metric?website=apple.com"
curl "http://localhost:5000/metric?website=microsoft.com"
curl "http://localhost:5000/metric?website=google.com"

# Automotive
curl "http://localhost:5000/metric?website=tesla.com"
curl "http://localhost:5000/metric?website=toyota.com"

# Consumer goods
curl "http://localhost:5000/metric?website=nike.com"
curl "http://localhost:5000/metric?website=cocacola.com"
```

---

## Troubleshooting

### Issue: LLM API Errors

**Symptoms**: Responses show `"status": "failed"` for one or more LLMs

**Solutions**:
1. Check API keys are valid
2. Verify API quotas/limits not exceeded
3. Check network connectivity
4. Review logs for specific error messages

### Issue: Database Connection Failed

**Symptoms**: 500 error, "database connection" in logs

**Solutions**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check DATABASE_URL is correct
3. Verify database exists: `psql -l | grep brank`
4. Check user permissions

### Issue: Slow Response Times

**Symptoms**: Requests taking > 60 seconds

**Solutions**:
1. Check LLM_TIMEOUT_SECONDS setting (increase if needed)
2. Verify network connection to LLM APIs
3. Reduce PROMPTS_N for faster testing
4. Check database query performance (indexes)

### Issue: Brand Not Extracted

**Symptoms**: Low mention_rate or null brandRank

**Possible Causes**:
1. Brand name not in known brands list (extractor limitation)
2. LLMs not mentioning the brand in responses
3. Prompts not relevant to brand

**Solutions**:
1. Check prompts generated in database
2. Review responses in database
3. Improve brand extraction logic if needed

---

## Load Testing (Optional)

Test concurrent requests:

```bash
# Install apache bench
brew install apache2  # macOS

# Send 10 requests with concurrency of 2
ab -n 10 -c 2 "http://localhost:5000/metric?website=samsung.com"
```

Monitor:
- Response times
- Database connection pool
- Memory usage
- Cache hit rate

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/postgres
        run: pytest -v --cov=.
```

---

## Next Steps

After verifying manual tests:
1. ✅ All endpoints respond correctly
2. ✅ Database records created properly
3. ✅ Metrics calculated accurately
4. ✅ Cache working (24h window)
5. ✅ Performance acceptable

You're ready for production deployment! 🎉

See `README.md` for deployment instructions.

