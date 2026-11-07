# Database migrations

CloudPilot uses SQLAlchemy models in `backend/models.py`. For the local MVP,
the FastAPI startup lifecycle creates the SQLite schema automatically when
`CLOUDPILOT_DATABASE_URL` is not set.

The same models support PostgreSQL by setting, for example:

```text
CLOUDPILOT_DATABASE_URL=postgresql+psycopg://user:password@localhost/cloudpilot
```

Alembic is configured in `alembic.ini` with the initial schema migration under
`migrations/versions/`. Local SQLite startup may still use `create_all` for
convenience; production and Compose deployments should run `alembic upgrade
head` before starting the API.
