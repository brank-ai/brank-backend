# Database Migration Rules

ALWAYS create an Alembic migration when modifying `db/models.py`:
- Add/remove/modify columns
- Add/remove tables
- Change column types, constraints, or indexes
- Modify relationships

## Migration Workflow
1. Edit models in `db/models.py`
2. Generate: `uv run alembic revision --autogenerate -m "descriptive message"`
3. Review the generated file in `alembic/versions/`
4. Apply: `uv run alembic upgrade head`

## Rules
- Use descriptive messages (e.g., "add status column to responses table" not "update db")
- One logical change per migration
- Verify `downgrade()` works
- CI workflow (`check-migrations.yml`) blocks PRs missing migrations for schema changes
