# Alembic migrations (WebGuard RF)

- **On startup:** If `USE_DATABASE=true` and `RUN_ALEMBIC_ON_STARTUP=true`, the API runs `alembic upgrade head` before accepting traffic (see `backend/app/db/migrate.py` and `session.py`).
- **Manual run** (from project root, with `.env` / DB credentials loaded):

```bash
cd "path/to/Random Forest-Sqli"
python -m alembic upgrade head
```

- **New revision** (after changing `backend/app/db/models.py`):

```bash
python -m alembic revision --autogenerate -m "describe_change"
python -m alembic upgrade head
```

Autogenerate requires a working database connection. Edit the generated file if needed, then upgrade.

## Existing database (tables already created by SQLAlchemy)

If tables already exist from a previous `create_all` and this is your first Alembic run, mark the current revision without re-running DDL:

```bash
python -m alembic stamp 001_initial
```

After that, normal `upgrade head` on startup will apply only **new** migrations.
