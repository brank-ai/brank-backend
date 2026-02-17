# /metric Pipeline Rules

The main endpoint `GET /metric?website=<brand_website>` runs a 4-step pipeline:

## Step 1: Prompt Generation
- ChatGPT generates N user questions where the brand could be relevant
- N configured via `PROMPTS_N` env var

## Step 2: Fetch LLM Responses
- Send all N prompts to 4 LLMs in parallel (ChatGPT, Gemini, Grok, Perplexity)
- Every network call must have a timeout (default 30s)
- Use retry with exponential backoff (tenacity)

## Step 3: Process Responses
- Extract `brands_list` (ordered list of brands mentioned) and `citation_list` (URLs) from each response
- Store in `responses` table

## Step 4: Calculate Metrics (per LLM independently)
- **brandRank**: Average 1-based position in brands_list (null if never appears)
- **citationsList**: Top 5 URLs by citation percentage
- **mentionRate**: responses_with_brand / total_responses (0.0 to 1.0)
- **sentimentScore**: 0-100 sentiment score

## Resilience
- Partial failures: if 1 LLM fails, return metrics for the other 3
- Never fail the entire request for a single LLM timeout
- 24-hour cache: check `metrics.updated_at` before running pipeline
