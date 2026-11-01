# Database migrations

CloudPilot uses SQLAlchemy models in `backend/models.py`. For the local MVP,
the FastAPI startup lifecycle creates the SQLite schema automatically when
`CLOUDPILOT_DATABASE_URL` is not set.

The same models support PostgreSQL by setting, for example:

```text
CLOUDPILOT_DATABASE_URL=postgresql+psycopg://user:password@localhost/cloudpilot
```

Alembic migration scripts will be added before introducing schema-changing
features. Until then, do not use `create_all` against a production database.
