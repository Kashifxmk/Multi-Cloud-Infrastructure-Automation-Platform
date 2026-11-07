# CloudPilot development status

## Current phase

Phase 14 - AWS read-only adapter.

## Completed

- Existing Python automation engine and Terraform provider structure retained.
- FastAPI backend added under `backend/`.
- Shared configuration validation exposed through the API.
- Safe local Terraform plan preview endpoint added.
- Local demo state and health endpoints added.
- Architecture and phased implementation plan documented.
- Existing CLI and local dashboard remain available.
- SQLAlchemy models added for users, organizations, RBAC membership, sessions,
  cloud accounts, configurations, deployments, costs, usage, and audit logs.
- Argon2id password hashing and HTTP-only session cookies added.
- Development email logging added for verification and password-reset links.
- Local authentication endpoints added without requiring an external email
  provider or cloud credentials.
- Registration, login, logout, protected profile, email verification, and
  password reset flows are covered by API tests.
- React/TypeScript/Vite frontend added under `frontend/`.
- Dashboard shell, responsive sidebar, authentication screens, local-demo
  empty states, and FastAPI dashboard integration added.
- FastAPI CORS is restricted to local Vite origins.
- Simulated AWS, GCP, and Azure account setup, connect, verify, list, and
  disconnect endpoints added.
- Account records are scoped to the authenticated user's organization.
- React Cloud Accounts modal added with explicit simulation labeling.
- Six infrastructure templates added with provider support, resource lists,
  difficulty, and estimated setup time.
- Authenticated template configuration save/list endpoints added.
- React template marketplace and four-step local configuration wizard added.
- Wizard validates provider, region, compute, and network fields before saving.
- Local AWS, GCP, and Azure pricing adapters added with normalized estimates.
- Cost comparison API added with explicit fixture source, assumptions, and
  live-data flag.
- React cost comparison modal added for compute, storage, database, and
  networking estimates.
- Frontend now hydrates `/api/auth/me` on startup, preserves authenticated
  sessions through refreshes, and provides sign-out.
- Fixed browser session persistence when using `localhost` by deriving the API
  host from the browser hostname, keeping frontend and cookie hosts consistent.
- Local architecture generation added from infrastructure configuration.
- React Flow architecture builder added with pan, zoom, controls, minimap, and
  generated resource relationships.
- Provider-specific Terraform preview generator added for AWS, GCP, and Azure.
- Generated `main.tf`, `variables.tf`, `outputs.tf`, and
  `terraform.tfvars.example` are available through the API and frontend.
- Terraform generation is explicitly local preview-only; no init, plan, apply,
  or cloud API call is performed.
- Simulated deployment plan, approval, provisioning, destroy, and history
  endpoints added.
- Sample resource IDs, deployment logs, and JSON reports are persisted locally.
- React deployment history modal added with explicit approval and destroy
  confirmation.
- Backend-enforced admin authorization added.
- Admin overview, user list, and audit-log endpoints added.
- Local admin bootstrap supported with `CLOUDPILOT_ADMIN_EMAIL`.
- React admin console added for authorized users.
- Docker Compose packaging added for PostgreSQL, FastAPI, and the React
  frontend.
- SQLite remains available for lightweight PowerShell development without
  containers.
- Shared organization membership lookup extracted into
  `backend/authorization.py`.
- Organization membership uniqueness enforced at the database model and
  migration level.
- Alembic configuration and initial schema migration added.
- Docker Compose now waits for PostgreSQL health before starting the backend.
- PostgreSQL startup uses `alembic upgrade head`; SQLite remains the only
  backend mode that creates tables automatically.
- Provider adapter contract added with explicit simulated AWS, Azure, and GCP
  implementations.
- Account verification now uses the provider registry and persists normalized
  identity, regions, capabilities, and simulation status.
- AWS read-only STS adapter added behind explicit
  `CLOUDPILOT_PROVIDER_MODE=real`; it uses the default credential chain,
  optional profile, or optional IAM role assumption and never accepts secret
  keys through the API.

## Test results

- Python unit and API tests: `24 passed` with `python -m pytest -q`.
- Frontend Vitest tests: `1 passed` with `npm test`.
- Frontend production build: passed with `npm run build`.
- Python compilation: passed with `python -m compileall -q backend core main.py`.
- Frontend production build: passed with `npm run build`.
- Health endpoint checks database connectivity and returns HTTP 503 when the
  configured database is unavailable.
- Container startup initializes the local MVP schema before serving API traffic.
- Existing sample configuration validation remains supported.
- No cloud credentials or paid cloud resources are required for Phase 9.

## Known limitations

- Authentication is local-development authentication; production OAuth, rate
  limiting, CSRF strategy for cross-site deployments, and secret management
  still require hardening.
- Development email links are intentionally emitted to backend logs.
- SQLite auto-creates the local schema; PostgreSQL deployments use Alembic
  migrations before API startup.
- The plan endpoint is a preview and deliberately does not execute Terraform.
- The new frontend includes dashboard, account, template, wizard, pricing,
  architecture, and simulated deployment foundations.
- Real cloud verification, pricing, deployment jobs, and full tenant policy
  enforcement are not implemented.
- Pricing uses local fixtures only; official provider pricing APIs are not
  connected.
- Architecture diagrams are local configuration previews and simulated
  deployments do not represent real provider resources.
- Generated Terraform is a preview and uses simplified provider resource
  examples; it is not an authenticated provider plan.
- Deployments are simulated only and do not create or modify cloud resources.
- Admin analytics are local database metrics; platform billing and production
  monitoring integrations are not implemented.
- Use the same hostname for the frontend and backend (`localhost` with
  `localhost`, or `127.0.0.1` with `127.0.0.1`) so browser cookies are sent.
- `npm install` reports transitive dependency audit findings; no forced
  breaking upgrade was applied.
- Docker Compose configuration validation passed. Docker image startup was not
  run because Docker Desktop's Linux engine was unavailable on the validation
  machine.
- Provider authentication, real provisioning, and full RBAC remain future
  phases.

## Next development gate

Next phase: Azure Entra and GCP workload-identity read-only adapters, retaining
simulation mode for credential-free testing.
