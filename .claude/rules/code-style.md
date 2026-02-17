# Code Style Rules

## Python Standards
- Type hints required on all public functions/methods (enforced by mypy)
- Formatting: Black (88 chars), isort (black profile)
- Linting: ruff (E, W, F, I, N, UP, B, C4)
- Docstrings: Google style for public APIs
- Never use bare `except:` — use specific exceptions
- Never use `import *`

## Naming
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants

## Logging
- DO log: request_id, brand_id, step names, durations, errors
- DON'T log: API keys, full LLM prompts/responses

## Don'ts
- Don't put business logic in Flask routes
- Don't use global variables for DB connections or HTTP clients
- Don't hardcode API keys, URLs, or configuration
- Don't make network calls without timeouts
- Don't create new patterns if existing ones work
