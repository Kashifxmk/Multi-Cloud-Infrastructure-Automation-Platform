# CloudPilot development status

## Current phase

Phase 9 - Simulated deployment lifecycle.

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

## Test results

- Python unit and API tests: `22 passed` with `python -m pytest -q`.
- Frontend production build: passed with `npm run build`.
- Existing sample configuration validation remains supported.
- No cloud credentials or paid cloud resources are required for Phase 9.

## Known limitations

- Authentication is local-development authentication; production OAuth, rate
  limiting, CSRF strategy for cross-site deployments, and secret management
  still require hardening.
- Development email links are intentionally emitted to backend logs.
- SQLite auto-creates the local schema; Alembic production migrations are not
  yet wired.
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
- Use the same hostname for the frontend and backend (`localhost` with
  `localhost`, or `127.0.0.1` with `127.0.0.1`) so browser cookies are sent.
- `npm install` reports transitive dependency audit findings; no forced
  breaking upgrade was applied.

## Next approval gate

Before Phase 10, review the simulated deployment lifecycle and approve admin
dashboard and usage analytics work.
