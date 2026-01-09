# Brank Backend Architecture

## Overview

Brank helps brands understand how Large Language Models (LLMs) perceive and recommend them. This backend service calculates brand visibility metrics by querying multiple LLMs with user-like questions and analyzing their responses.

## System Architecture

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ GET /metric?website=samsung.com
       ▼
┌──────────────────────────────────────────────────┐
│              Flask API Server                    │
│  ┌────────────────────────────────────────────┐ │
│  │  /metric Endpoint (api/routes.py)          │ │
│  └─────────────────┬──────────────────────────┘ │
│                    ▼                             │
│  ┌────────────────────────────────────────────┐ │
│  │  Metric Service (services/)                │ │
│  │  1. Check 24h cache                        │ │
│  │  2. If stale → run pipeline                │ │
│  └─────────────────┬──────────────────────────┘ │
└──────────────────┬─┴──────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │   Pipeline Orchestration     │
    └──────────────────────────────┘
              │
              ├─► Step 1: Prompt Generation (ChatGPT)
              │   Generate N user questions
              │
              ├─► Step 2: LLM Queries (Parallel)
              │   ├─► ChatGPT
              │   ├─► Gemini  
              │   ├─► Grok
              │   └─► Perplexity
              │
              ├─► Step 3: Response Processing
              │   Extract brands_list, citation_list
              │
              └─► Step 4: Metrics Calculation
                  Calculate per-LLM metrics
                  
                   ▼
    ┌──────────────────────────────┐
    │   PostgreSQL Database        │
    │   - brands                   │
    │   - prompts                  │
    │   - responses                │
    │   - metrics                  │
    │   - time_profiling           │
    └──────────────────────────────┘
```

## Request Flow

### Happy Path (Fresh Computation)

1. **Client Request**: `GET /metric?website=samsung.com`

2. **Cache Check**:
   - Query `metrics` table for `brand_id` with matching website
   - Check if `updated_at` < 24 hours ago
   - If fresh → return cached metrics
   - If stale/missing → proceed to pipeline

3. **Step 1: Prompt Generation** (~2-5 seconds)
   - Query ChatGPT: "Generate {N} questions users might ask where {brand} could be relevant"
   - Parse response into list of prompts
   - Store in `prompts` table

4. **Step 2: LLM Queries** (~10-20 seconds, parallel)
   - For each prompt, query all 4 LLMs simultaneously
   - Use thread pool or async for parallelism
   - Timeout: 30s per LLM call
   - Retry: 3 attempts with exponential backoff

5. **Step 3: Process Responses** (~1-2 seconds)
   - For each response:
     - Extract ordered list of brands mentioned
     - Extract all URLs/citations
   - Store in `responses` table with `llm_name`

6. **Step 4: Calculate Metrics** (~1 second)
   - For each LLM independently:
     - **brandRank**: Average position of brand
     - **citationsList**: Top 5 URLs by percentage
     - **mentionRate**: Fraction of responses with brand
     - **sentimentScore**: Sentiment analysis (0-100)
   - Store in `metrics` table (4 rows, one per LLM)

7. **Persist Timing**: Store step durations in `time_profiling`

8. **Response**: Return JSON with metrics per LLM

### Cached Path

1. Client request arrives
2. Cache check finds fresh metrics (< 24h)
3. Return cached data immediately (~50ms)

## Database Schema

### Entity Relationship Diagram

```
brands (1) ──< (N) prompts
               │
               └──< (N) responses
                         │
                         └─ llm_name (chatgpt|gemini|grok|perplexity)

brands (1) ──< (N) metrics
                    │
                    └─ llm_name (per LLM metrics)

brands (1) ──< (N) time_profiling
```

### Table Details

#### brands
Primary entity representing a brand.

| Column     | Type      | Constraints         | Description           |
|------------|-----------|---------------------|-----------------------|
| brand_id   | UUID      | PRIMARY KEY         | Unique identifier     |
| name       | VARCHAR   | NOT NULL            | Brand name            |
| website    | VARCHAR   | UNIQUE, NOT NULL    | Brand website URL     |
| created_at | TIMESTAMP | DEFAULT NOW()       | Creation timestamp    |
| updated_at | TIMESTAMP | DEFAULT NOW()       | Last update timestamp |

**Indexes**: `website`, `brand_id`

#### prompts
Questions generated for a brand.

| Column     | Type      | Constraints              | Description                    |
|------------|-----------|--------------------------|--------------------------------|
| prompt_id  | UUID      | PRIMARY KEY              | Unique identifier              |
| brand_id   | UUID      | FOREIGN KEY → brands     | Associated brand               |
| prompt     | TEXT      | NOT NULL                 | Question text                  |
| created_at | TIMESTAMP | DEFAULT NOW()            | Creation timestamp             |
| updated_at | TIMESTAMP | DEFAULT NOW()            | Last update timestamp          |

**Indexes**: `brand_id`, `prompt_id`

#### responses
LLM responses to prompts.

| Column        | Type      | Constraints              | Description                      |
|---------------|-----------|--------------------------|----------------------------------|
| response_id   | UUID      | PRIMARY KEY              | Unique identifier                |
| prompt_id     | UUID      | FOREIGN KEY → prompts    | Associated prompt                |
| llm_name      | VARCHAR   | NOT NULL                 | 'chatgpt'\|'gemini'\|'grok'\|'perplexity' |
| answer        | TEXT      | NOT NULL                 | Full LLM response text           |
| brands_list   | JSON      | NOT NULL                 | Ordered array of brand names     |
| citation_list | JSON      | NOT NULL                 | Array of URLs                    |
| created_at    | TIMESTAMP | DEFAULT NOW()            | Creation timestamp               |
| updated_at    | TIMESTAMP | DEFAULT NOW()            | Last update timestamp            |

**Indexes**: `(prompt_id, llm_name)`, `llm_name`

**Example Row**:
```json
{
  "response_id": "uuid",
  "prompt_id": "uuid",
  "llm_name": "chatgpt",
  "answer": "For phones under $500, I'd recommend Samsung Galaxy A54, Google Pixel 7a...",
  "brands_list": ["Samsung", "Google", "Motorola"],
  "citation_list": ["https://samsung.com/...", "https://gsmarena.com/..."]
}
```

#### metrics
Calculated metrics per brand per LLM.

| Column          | Type      | Constraints              | Description                         |
|-----------------|-----------|--------------------------|-------------------------------------|
| metric_id       | UUID      | PRIMARY KEY              | Unique identifier                   |
| brand_id        | UUID      | FOREIGN KEY → brands     | Associated brand                    |
| llm_name        | VARCHAR   | NOT NULL                 | 'chatgpt'\|'gemini'\|'grok'\|'perplexity' |
| mention_rate    | FLOAT     | NOT NULL                 | 0.0 - 1.0                          |
| citations_list  | JSON      | NOT NULL                 | Top 5 URLs with percentages         |
| sentiment_score | FLOAT     | NOT NULL                 | 0.0 - 100.0                        |
| brand_rank      | FLOAT     | NULLABLE                 | Average rank, null if never appears |
| created_at      | TIMESTAMP | DEFAULT NOW()            | Creation timestamp                  |
| updated_at      | TIMESTAMP | DEFAULT NOW()            | Last computation timestamp          |

**Indexes**: `(brand_id, llm_name)`, `(brand_id, updated_at)`

**Example Row**:
```json
{
  "metric_id": "uuid",
  "brand_id": "uuid",
  "llm_name": "chatgpt",
  "mention_rate": 0.8,
  "citations_list": [
    {"url": "https://samsung.com/...", "percentage": 80.0},
    {"url": "https://gsmarena.com/...", "percentage": 60.0}
  ],
  "sentiment_score": 75.5,
  "brand_rank": 1.75,
  "updated_at": "2026-01-09T10:30:00Z"
}
```

#### time_profiling
Performance metrics per request.

| Column                      | Type      | Constraints              | Description                  |
|-----------------------------|-----------|--------------------------|------------------------------|
| profile_id                  | UUID      | PRIMARY KEY              | Unique identifier            |
| brand_id                    | UUID      | FOREIGN KEY → brands     | Associated brand             |
| request_id                  | UUID      | NOT NULL                 | Unique request identifier    |
| prompt_generation_time      | FLOAT     | NOT NULL                 | Seconds                      |
| fetching_llm_response_time  | FLOAT     | NOT NULL                 | Seconds (parallel duration)  |
| processing_response_time    | FLOAT     | NOT NULL                 | Seconds                      |
| metrics_calculation_time    | FLOAT     | NOT NULL                 | Seconds                      |
| created_at                  | TIMESTAMP | DEFAULT NOW()            | Creation timestamp           |

**Indexes**: `brand_id`, `request_id`

## Metric Calculation Algorithms

### 1. brandRank

**Input**: List of responses for one LLM, each with `brands_list`

**Algorithm**:
```python
def calculate_brand_rank(brand_name: str, responses: list[Response]) -> float | None:
    """
    Calculate average position of brand across responses.
    
    Returns:
        Average 1-based rank, or None if brand never appears
    """
    ranks = []
    normalized_brand = normalize_brand_name(brand_name)
    
    for response in responses:
        normalized_list = [normalize_brand_name(b) for b in response.brands_list]
        
        if normalized_brand in normalized_list:
            # 1-based index
            rank = normalized_list.index(normalized_brand) + 1
            ranks.append(rank)
    
    if not ranks:
        return None
    
    return sum(ranks) / len(ranks)
```

**Example**:
- Prompt 1: `["Apple", "Samsung", "Google"]` → Samsung rank = 2
- Prompt 2: `["Samsung", "Xiaomi"]` → Samsung rank = 1
- Prompt 3: `["Google", "Apple"]` → Samsung not present (skip)
- **Result**: `(2 + 1) / 2 = 1.5`

### 2. citationsList

**Input**: List of responses for one LLM, each with `citation_list`

**Algorithm**:
```python
def calculate_citations_list(responses: list[Response]) -> list[dict]:
    """
    Calculate top 5 URLs by citation percentage.
    
    Returns:
        List of {url, percentage} sorted by percentage desc
    """
    url_counts = Counter()
    total_responses = len(responses)
    
    for response in responses:
        # Dedupe URLs within single response
        unique_urls = set(canonicalize_url(url) for url in response.citation_list)
        url_counts.update(unique_urls)
    
    # Calculate percentages
    citations = [
        {
            "url": url,
            "percentage": round((count / total_responses) * 100, 2)
        }
        for url, count in url_counts.items()
    ]
    
    # Sort by percentage desc, then count desc
    citations.sort(key=lambda x: (-x["percentage"], -url_counts[x["url"]]))
    
    return citations[:5]
```

**URL Canonicalization**:
- Lowercase hostname
- Remove trailing slash
- Remove common tracking params (`?utm_*`, `?ref=`, etc.)
- Keep path and important query params

### 3. mentionRate

**Input**: List of responses for one LLM

**Algorithm**:
```python
def calculate_mention_rate(brand_name: str, responses: list[Response]) -> float:
    """
    Calculate fraction of responses that mention the brand.
    
    Returns:
        Float between 0.0 and 1.0
    """
    normalized_brand = normalize_brand_name(brand_name)
    mentions = 0
    
    for response in responses:
        normalized_list = [normalize_brand_name(b) for b in response.brands_list]
        if normalized_brand in normalized_list:
            mentions += 1
    
    return mentions / len(responses)
```

**Example**:
- 10 prompts sent to ChatGPT
- Samsung mentioned in 8 responses
- **Result**: `8 / 10 = 0.8`

### 4. sentimentScore

**Input**: Responses mentioning the brand

**Algorithm** (using sentiment analysis library or LLM):
```python
def calculate_sentiment_score(brand_name: str, responses: list[Response]) -> float:
    """
    Calculate sentiment toward brand (0=negative, 100=positive).
    
    Returns:
        Float between 0.0 and 100.0
    """
    relevant_responses = [
        r for r in responses 
        if brand_name in r.brands_list
    ]
    
    if not relevant_responses:
        return 50.0  # Neutral if brand never mentioned
    
    sentiments = []
    for response in relevant_responses:
        # Extract sentences mentioning brand
        sentences = extract_brand_context(response.answer, brand_name)
        
        # Analyze sentiment (using library or LLM)
        sentiment = analyze_sentiment(sentences)  # Returns -1 to 1
        
        # Convert to 0-100 scale
        score = (sentiment + 1) * 50
        sentiments.append(score)
    
    return sum(sentiments) / len(sentiments)
```

**Options for Sentiment Analysis**:
1. Use sentiment analysis library (TextBlob, VADER)
2. Use LLM to classify sentiment (more accurate but slower)
3. Hybrid: library for quick scan, LLM for edge cases

## LLM Client Integration

### Abstract Base Client

```python
from abc import ABC, abstractmethod
from typing import Protocol

class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    @abstractmethod
    def query(self, prompt: str, timeout: int = 30) -> str:
        """Send prompt to LLM and return response text.
        
        Args:
            prompt: Question to send
            timeout: Max seconds to wait
            
        Returns:
            Response text
            
        Raises:
            LLMTimeoutError: If request times out
            LLMAPIError: If API returns error
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return LLM name: 'chatgpt'|'gemini'|'grok'|'perplexity'"""
        pass
```

### Provider-Specific Clients

Each provider has its own client implementing the protocol:

- `ChatGPTClient` - uses OpenAI SDK
- `GeminiClient` - uses Google Generative AI SDK
- `GrokClient` - uses xAI API
- `PerplexityClient` - uses Perplexity API

All clients handle:
- Authentication (API keys from env)
- Retries with exponential backoff
- Timeout enforcement
- Error mapping to common exceptions

## Caching Strategy

### 24-Hour Cache Window

```python
from datetime import datetime, timedelta

def is_cache_valid(updated_at: datetime) -> bool:
    """Check if cached metrics are still fresh."""
    now = datetime.utcnow()
    age = now - updated_at
    return age < timedelta(hours=24)
```

### Cache Lookup

```sql
SELECT * FROM metrics
WHERE brand_id = :brand_id
  AND updated_at > NOW() - INTERVAL '24 hours'
```

If all 4 LLMs have fresh metrics → return cached  
If any LLM is stale → recompute all (ensures consistency)

## Error Handling

### Partial Failures

If one LLM fails, still return results for others:

```json
{
  "brand_id": "uuid",
  "website": "samsung.com",
  "metrics": {
    "chatgpt": { /* successful metrics */ },
    "gemini": { /* successful metrics */ },
    "grok": {
      "error": "Timeout after 30s",
      "status": "failed"
    },
    "perplexity": { /* successful metrics */ }
  }
}
```

### HTTP Status Codes

- `200 OK`: Success (including partial failures)
- `400 Bad Request`: Invalid website parameter
- `404 Not Found`: Brand not found (if applicable)
- `500 Internal Server Error`: Complete failure
- `503 Service Unavailable`: All LLMs down

## Performance Considerations

### Expected Timings

| Step                  | Duration    | Parallelizable |
|-----------------------|-------------|----------------|
| Cache check           | ~50ms       | No             |
| Prompt generation     | ~2-5s       | No             |
| LLM queries (4 LLMs)  | ~10-20s     | Yes (parallel) |
| Response processing   | ~1-2s       | Partially      |
| Metrics calculation   | ~1s         | Yes (per LLM)  |
| **Total (fresh)**     | **~15-30s** | -              |
| **Total (cached)**    | **~50ms**   | -              |

### Optimization Strategies

1. **Parallel LLM Queries**: Use thread pool to query all 4 LLMs simultaneously
2. **Connection Pooling**: Reuse HTTP connections to LLM APIs
3. **Database Indexing**: Index frequently queried columns
4. **Response Streaming**: Stream results to client as they arrive (future enhancement)

## Security

### API Key Management

- Store in environment variables
- Never log or expose in responses
- Rotate regularly
- Use separate keys for dev/prod

### Input Validation

```python
def validate_website(website: str) -> str:
    """Validate and normalize website URL."""
    # Remove protocol
    website = website.lower().strip()
    website = website.removeprefix("http://").removeprefix("https://")
    website = website.removeprefix("www.")
    
    # Validate format
    if not re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', website):
        raise ValueError("Invalid website format")
    
    return website
```

### Rate Limiting

Consider adding rate limiting to prevent abuse:
- Per IP: 10 requests per minute
- Per brand: 1 request per hour (enforced by cache)

## Future Enhancements

1. **Streaming Results**: Return metrics as they're computed
2. **Historical Tracking**: Track metric changes over time
3. **Alerting**: Notify brands of significant rank changes
4. **More LLMs**: Add Claude, Llama, etc.
5. **Custom Prompts**: Allow brands to provide their own questions
6. **Competitor Analysis**: Compare brand vs competitors
7. **Geographic Targeting**: Different metrics per region

## Deployment

### Environment Variables

```bash
# LLM API Keys
CHATGPT_API_KEY=sk-...
GEMINI_API_KEY=...
GROK_API_KEY=...
PERPLEXITY_API_KEY=...

# Configuration
PROMPTS_N=10
DATABASE_URL=postgresql://user:pass@host:5432/brank
LLM_TIMEOUT_SECONDS=30
MAX_RETRIES=3

# Flask
FLASK_ENV=production
SECRET_KEY=...
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add metrics table"

# Apply migrations
alembic upgrade head
```

### Running the Server

```bash
# Install dependencies
uv pip install -e .

# Run migrations
alembic upgrade head

# Start server
flask run --host=0.0.0.0 --port=5000
```

## Testing Strategy

### Unit Tests
- Metric calculation functions
- Brand/URL extraction
- Cache validation logic

### Integration Tests
- Full `/metric` endpoint
- Database operations
- LLM client mocking

### Load Tests
- Concurrent requests
- Cache hit rates
- Database connection pooling

## Monitoring

### Key Metrics to Track

- Request latency (p50, p95, p99)
- Cache hit rate
- LLM API success rate
- Database query times
- Error rates per LLM

### Logging

Use structured logging with:
- `request_id`: Unique per request
- `brand_id`: Brand being analyzed
- `step`: Pipeline step name
- `duration_ms`: Step duration
- `llm_name`: Which LLM (for step 2-4)

---

**Last Updated**: January 9, 2026  
**Version**: 0.1.0

