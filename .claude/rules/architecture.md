# Architecture Rules

## Mandatory Layer Separation
- API routes (`api/`) must NOT contain business logic — validate input, get dependencies, call service, return response
- Services (`services/`) must NOT import Flask objects
- DB access only through repositories (`db/repositories/`)
- All external calls isolated behind client interfaces (`llm_clients/`)

## Dependency Injection (Prevent Memory Leaks)
ALWAYS pass dependencies explicitly as function/method parameters. Never use global singletons for DB connections or HTTP clients.

```python
# CORRECT
def calculate_metrics(
    brand_id: str,
    db_session: Session,
    llm_clients: dict[str, LLMClient],
    logger: Logger
) -> dict:
    data = db_session.query(...)

# WRONG - causes memory leaks
db_session = create_session()  # global singleton
def calculate_metrics(brand_id: str):
    data = db_session.query(...)
```

## Flask Patterns
- Use application factory: `def create_app() -> Flask`
- Use `flask.g` or request-scoped objects for DB sessions
- SQLAlchemy: use `scoped_session`
- Create LLM clients per request or use proper connection pooling
