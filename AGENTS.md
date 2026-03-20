# AGENTS.md

## Project overview

This repository is a personal **electronic lab notebook** web application.
It is implemented as a small monorepo with:

- `apps/api`: backend API
- `apps/web`: frontend web app

The product is centered on **experiment-oriented structured work**, not a generic CMS or pure chat app.

The current implemented scope is already broader than the earliest MVP:
- authentication and session restore
- project management
- template management
- record create / edit / detail / list
- attachment upload / download
- record version snapshots
- audit logs
- user/AI settings
- AI assistant integration boundary

Core principle:
**projects, templates, and records remain the center of the system.**
Audit, AI, settings, and molecule-related enhancements are supporting capabilities, not the product core.

---

## Repository structure

### Root
Key files and folders currently include:

- `apps/`
- `.env.example`
- `docker-compose.yml`
- `package.json`
- `pnpm-workspace.yaml`

Root package manager and scripts:
- package manager: `pnpm`
- web dev entry from root: `pnpm dev:web`
- web build entry from root: `pnpm build:web`

### Backend: `apps/api`
Current backend structure includes:

- `alembic/`
- `alembic.ini`
- `pyproject.toml`
- `scripts/`
- `app/`

Inside `apps/api/app/` the structure is organized by responsibility:

- `api/`
- `core/`
- `db/`
- `models/`
- `schemas/`
- `services/`
- `main.py`

This means the backend is already organized as a layered FastAPI application and should remain so.

### Frontend: `apps/web`
Current frontend structure includes:

- `public/`
- `src/`
- `index.html`
- `package.json`
- `vite.config.ts`
- TypeScript config files

Inside `apps/web/src/` the current structure includes:

- `api/`
- `assets/`
- `components/`
- `router/`
- `stores/`
- `types/`
- `utils/`
- `views/`
- `App.vue`
- `main.ts`

Do not flatten this structure into an unorganized view-heavy frontend.

---

## Confirmed stack and runtime assumptions

### Frontend
Use and preserve the current frontend direction:

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router
- Axios

The frontend currently also carries:
- `ketcher-react`
- `ketcher-standalone`
- `react`
- `react-dom`

This likely exists to support chemistry/molecule editing integration.
Do not casually remove these dependencies unless you have confirmed they are truly unused.

### Backend
Use and preserve the current backend direction:

- FastAPI
- SQLAlchemy
- Alembic
- psycopg / PostgreSQL
- pydantic-settings
- JWT-based auth
- multipart upload support

### Infrastructure
- Local database is currently expected to be PostgreSQL
- `docker-compose.yml` currently provisions PostgreSQL only
- file storage is currently local-first
- upload directory is environment-configurable
- LLM runtime is configurable by environment and frontend settings

---

## Product scope: what this app is

This app is a **lab workflow notebook** centered around structured experiment records.

Current first-class business areas are:

1. auth
2. projects
3. templates
4. records
5. attachments
6. versions / snapshots
7. audit logs
8. AI runtime settings and assistant entry

Important:
- `projects`, `templates`, and `records` are the business core
- `attachments`, `versions`, and `audit logs` are traceability/support layers
- `AI settings` and `assistant` are enhancement layers
- chemistry-specific capability should remain additive, not distort the whole data model

Do not let AI capability replace notebook capability.

---

## Current route-level mental model

### Backend routes
The backend router currently includes at least:

- health
- auth
- templates
- projects
- records
- attachments
- versions
- audit logs
- llm

When changing backend routing:
- keep route naming consistent
- avoid breaking existing prefixes
- avoid moving endpoints without updating all frontend callers in the same task

### Frontend routes
The frontend currently has authenticated routes for at least:

- `/projects`
- `/templates`
- `/records`
- `/records/new`
- `/records/:id`
- `/records/:id/edit`
- `/audit-logs` (admin-only)

The codebase also contains user/AI settings related UI and store logic.
Treat settings as a real part of the application shell, not as throwaway experimental code.

Do not break:
- login redirect behavior
- session restore behavior
- admin-only route guard behavior
- authenticated navigation shell behavior

---

## Non-negotiable product invariants

These flows must remain intact unless the task explicitly changes them:

### Auth and entry
- login works
- logout works
- session restore works
- protected routes redirect correctly
- admin-only routes remain protected

### Core business loop
- project list/create/edit/delete still works
- template list/create/edit/delete still works
- record list/create/edit/detail still works

### Traceability
- attachment upload/download still works
- version snapshot viewing still works
- audit logs remain accessible for appropriate roles

### UX shell
- authenticated navigation remains visible
- logout action must remain visible and usable
- key entry points to projects/templates/records must remain reachable

A previous failure pattern in this project was losing visible CRUD entry points while keeping partial login/browse functionality.
Do not repeat that.

---

## AI-related rules

This repository already contains AI-related backend routes and frontend state.
Treat AI as a bounded subsystem.

### What to preserve
- AI configuration should remain manageable from settings-oriented UI, not scattered across random pages
- local model mode remains a valid default
- API-key mode is a supported override path
- frontend AI config persistence should remain predictable
- backend LLM configuration should stay environment-driven and explicit

### What to avoid
- do not hardwire the whole product to a single model vendor
- do not make project/template/record flows depend on live AI availability
- do not move business validation into LLM calls
- do not add magical hidden prompts or opaque behavior without configuration visibility

AI failure should degrade gracefully, not block notebook basics.

---

## Backend implementation rules

### Layering
Keep responsibilities separated:

- `api/`: routing and request wiring
- `schemas/`: validation and API contracts
- `models/`: persistence models
- `services/`: business logic
- `db/`: session/database wiring
- `core/`: settings/security/core helpers

Do not push all logic into route handlers.

### Migrations
Because Alembic is present:

- schema changes should be accompanied by migration updates when applicable
- do not silently change DB models without checking migration impact
- avoid destructive schema changes unless explicitly required

### API contracts
When modifying backend responses:
- update frontend types and API callers in the same task
- preserve backward-compatible field names when possible
- avoid casual response-shape churn

### Files and storage
Because attachments are part of the product:
- do not change upload behavior without checking download and record detail flows
- do not hardcode local paths that differ from configured storage behavior

---

## Frontend implementation rules

### State and routing
The frontend already uses stores and route guards.
Therefore:

- auth logic belongs in stores/utilities, not duplicated in every view
- route access rules should remain centralized
- session restore should not be reimplemented ad hoc
- admin-only behavior should not be enforced only in the UI layer

### View responsibilities
Views under `src/views/` are page-level entry points.
Keep heavy reusable logic in:
- `components/`
- `stores/`
- `api/`
- `utils/`

Do not let each page become a giant self-contained system.

### Business-critical pages
Be especially careful when changing:

- `LoginView`
- `ProjectsView`
- `TemplatesView`
- `RecordsView`
- `RecordCreateView`
- `RecordDetailView`
- `RecordEditView`
- audit-log related pages
- settings / AI configuration related pages
- `App.vue` authenticated shell

### Shell and navigation
The main application shell already carries:
- authenticated navigation
- user info area
- logout entry
- AI-related entry points

Do not remove or hide these by accident during layout refactors.

---

## Chemistry / rich editor caution

The presence of Ketcher-related dependencies suggests chemistry-oriented structure editing is planned or partially integrated.

Therefore:
- do not remove React bridge dependencies casually
- do not assume the frontend is “pure Vue only” at the dependency level
- isolate chemistry-specific UI so it extends the notebook rather than reshaping the whole app
- preserve future compatibility for specialized scientific templates

---

## Local development assumptions

### Root-level web commands
Run from repository root when possible:

- `pnpm dev:web`
- `pnpm build:web`
- `pnpm preview:web`

### Frontend local development
- Vite dev server is expected on port `5173`
- when `VITE_API_BASE_URL` is absent, the dev environment may proxy `/api` to the backend

### Backend local development
Backend entrypoint is `apps/api/app/main.py`.
Typical local run should be based on `app.main:app` from within `apps/api`.

Do not hardcode a different startup assumption unless the repo is updated accordingly.

### Database
Use the provided PostgreSQL service definition as the default local DB baseline.
Do not silently switch the project to SQLite or another DB without explicit intent.

---

## Change-impact rules

When touching one area, check the linked areas.

### If you change auth
Also verify:
- frontend auth store
- route guards
- login page
- logout flow
- current-user fetch
- role-based UI behavior

### If you change records
Also verify:
- record list
- create/edit/detail pages
- template compatibility
- attachments
- versions / snapshots

### If you change templates
Also verify:
- record creation flow
- record editing flow
- any schema-driven rendering assumptions

### If you change AI config/runtime
Also verify:
- settings page
- AI store persistence
- shell AI status display
- backend LLM status/check endpoints

### If you change audit behavior
Also verify:
- admin-only access
- backend permissions
- frontend navigation exposure

---

## Git workflow

### Branching
Use one short-lived branch per task:

- `feat/...`
- `fix/...`
- `refactor/...`
- `docs/...`
- `chore/...`

Examples:
- `feat/record-version-panel`
- `fix/logout-redirect`
- `fix/template-form-validation`
- `refactor/record-service-split`

### Pull requests
Keep PRs narrow:
- one feature
- one bugfix
- one refactor theme
- one documentation change

Do not bundle unrelated cleanup with business logic changes.

### Main branch
- avoid direct pushes to `main`
- prefer PR merge workflow
- keep `main` releasable/stable

---

## What should go into AGENTS.md vs elsewhere

### AGENTS.md should contain
- product direction
- repository structure
- stable build/run/test conventions
- architecture rules
- protected invariants
- coding workflow rules
- critical warnings

### AGENTS.md should NOT become
- a changelog
- a weekly diary
- a task queue
- a bug backlog
- a meeting note dump

Use other files for that, such as:
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `CHANGELOG.md`
- issue tracker / PR descriptions

---

## When to update this file

Update `AGENTS.md` only when one of these changes:

1. product direction changes
2. repository structure changes
3. build/run/test commands change
4. branch/PR workflow changes
5. core invariants change
6. forbidden areas / security constraints change
7. a new subsystem becomes long-term and first-class

Do **not** update it for every small feature, bugfix, or one-off experiment.

---

## Definition of done

A task is not done just because code compiles.

A task is closer to done when:
- it respects the notebook product direction
- it preserves auth + navigation + CRUD core flows
- it keeps projects/templates/records as the center
- it does not break attachments, versions, or auditability
- it keeps AI as an enhancement layer rather than a hard dependency
- it updates both frontend and backend when contracts change
- it leaves the repo easier to continue

---

## Final decision rule

When unsure, ask:

**Does this change make the repository a better electronic lab notebook without breaking the current authenticated workflow and core project/template/record loop?**

If not, reconsider the approach.