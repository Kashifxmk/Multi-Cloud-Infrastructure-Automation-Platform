# CloudPilot implementation plan

## Completed: Phase 1

- Inspected the existing Python CLI, validator, Terraform manager, sample
  configurations, provider entrypoints, Ansible playbook, tests, and local demo UI.
- Added a FastAPI application while preserving the existing CLI and UI.
- Reused the existing validator and provider-directory selection logic.
- Added local-only API endpoints and tests.
- Documented the migration architecture and local run commands.

## Next phases

1. Authentication, PostgreSQL models, organizations, RBAC, and tenant isolation.
2. React/TypeScript application shell and protected navigation.
3. Secure cloud-account connection workflows with provider-specific verification.
4. Template catalog and configuration wizard backed by Terraform modules.
5. Pricing adapters with explicit unavailable-data states.
6. Architecture visualization from validated plans.
7. Redis/Celery deployment jobs and approval lifecycle.
8. Assistant foundation, analytics, subscriptions, security testing, and release hardening.

Each phase must preserve the CLI, avoid fabricated live data, and pass focused
tests before the next phase begins.
