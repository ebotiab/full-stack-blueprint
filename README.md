# full-stack-blueprint

A [Copier](https://copier.readthedocs.io) template for a web project with a Python API and a
TypeScript visor, ready to work on from the first minute: by people, and above all by coding
agents (Claude Code, Codex, Cursor…), which get an `AGENTS.md`, skills and a `Makefile` whose
targets never prompt and always end with a clear exit code and summary.

## Built for development with coding agents

The template assumes that you direct the work and a coding agent writes most of the code. Every
choice follows from that: code an agent can read and verify beats abstraction that saves a person
typing, and every check gives a clear verdict the agent can act on without asking.

- **SQL, no ORM.** Queries are plain SQL run with asyncpg, next to the code that uses them, and a
  schema change is a numbered `.sql` file. An ORM saves people from writing SQL and mapping rows by
  hand; for an agent that work is cheap, while an ORM adds a second language and queries generated
  out of sight. Plain SQL is what an agent writes, reviews and tests most reliably.
- **Contracts that machines check.** Types on both sides, an OpenAPI schema committed with the
  code, TypeScript types generated from it and tests against a real PostgreSQL: when any of them
  drifts the CI fails, so a mistake shows up as a failed check instead of a bug in production.
- **Commands that never ask.** Every `make` target runs without prompts and ends with a reliable
  exit code and a summary of what passed and failed.
- **Instructions in the repository.** Each project gets an `AGENTS.md` (Claude Code reads it
  through `CLAUDE.md`; Codex, Cursor and others read it directly) and skills for its usual tasks,
  such as changing the API or shipping a change.
- **Production the agent can check.** `obs status` reads the traces in Logfire and tells whether a
  commit is deployed and serving without errors, so a task ends when production confirms it.

What a generated project contains:

- **API** (`backend/`): Python 3.13 with uv and uv_build, FastAPI, asyncpg without an ORM and a
  small packaged SQL migration runner (idempotent, PostgreSQL advisory lock, checksums),
  pydantic-settings, a Typer CLI (`migrate`, `openapi`, `obs status`), Logfire (works without a
  token), pytest against a real PostgreSQL, ruff, and pyright or ty.
- **Visor** (`frontend/`, optional): Vite 8, React 19, TypeScript 7, a client typed from the API's
  OpenAPI schema (`openapi-typescript` + `openapi-fetch`), oxlint, oxfmt (exact version), Vitest,
  Playwright, `@pydantic/logfire-browser` and Vercel Web Analytics.
- **Database** (optional): PostgreSQL 17 in docker-compose for development; Neon in production.
- **Deploy**: the API on Render (default), FastAPI Cloud, Railway or Vercel; the visor on Vercel.
  Only the chosen target's files are generated, in an EU region wherever the platform has one.
- **Repository**: a CI that skips the half a pull request does not touch and fails when the
  OpenAPI schema or the generated types are stale, grouped Dependabot updates, VS Code settings
  that match the checks.

## Generate a project

Install Copier once (`uv tool install copier`), then:

```bash
copier copy gh:ebotiab/full-stack-blueprint my-project
```

Copier asks each question with its default. To generate without any prompt (what agents do), take
the defaults and override what you need:

```bash
copier copy --defaults \
  --data project_name="Bus Stops" \
  --data api_deploy=railway \
  gh:ebotiab/full-stack-blueprint bus-stops
```

or put the answers in a file: `copier copy --defaults --data-file answers.yml gh:ebotiab/full-stack-blueprint bus-stops`.
The template has no `_tasks`, so `--trust` is never needed. Then, inside the project:

```bash
git init && git add -A && git commit -m "Generate from full-stack-blueprint"
make doctor   # checks uv, Node and Docker and says how to fix what is missing
make setup    # dependencies, PostgreSQL, migrations, API schema and types
make check    # everything the CI runs
git add -A && git commit -m "Lockfiles and generated API types"
```

## Options and defaults

| Question | Default | Values |
| --- | --- | --- |
| `project_name` | `My Project` | any text |
| `project_slug` | from the name (`my-project`) | kebab-case: repository, CLI command, service names |
| `package_name` | from the slug (`my_project`) | Python package |
| `env_prefix` | from the package (`MY_PROJECT_`) | prefix of the project's environment variables |
| `description` | `A FastAPI API with a React visor.` | one sentence |
| `github_repo` | `your-github-user/<slug>` | `owner/name`; used for links, Logfire and Railway |
| `with_frontend` | `true` | include the visor |
| `with_database` | `true` | include PostgreSQL |
| `postgres_port` | `5434` | host port of the local PostgreSQL (asked only with a database) |
| `type_checker` | `pyright` | `pyright`, `ty` |
| `api_deploy` | `render` | `render`, `fastapi_cloud`, `railway`, `vercel` |
| `api_public_url` | the platform's usual URL | where the visor's `vercel.json` proxies `/api` (asked only with a visor and a non-Vercel API) |

Two defaults are meant to change, each with a one-line edit in `copier.yml` (the comment above the
question says which line):

- **`type_checker: ty`** once ty publishes a stable 1.0 release. Until then it is a 0.0.x beta:
  faster than pyright, but its diagnostics still change between releases.
- **`api_deploy: fastapi_cloud`** once FastAPI Cloud offers all of: an EU region, a Dockerfile or a
  command that runs before start-up (for migrations), rollbacks that are no longer "coming soon",
  and active usage-based billing. Until then Render is the default: Docker, Frankfurt, a free plan.

What each deploy target generates:

| `api_deploy` | Files | Migrations run | Deployed commit read from |
| --- | --- | --- | --- |
| `render` | `backend/Dockerfile`, `render.yaml` | at API start-up (free plan has no pre-deploy) | `RENDER_GIT_COMMIT` |
| `fastapi_cloud` | `[tool.fastapi] entrypoint`, `.github/workflows/deploy-api.yml` | at API start-up | `backend/DEPLOYED_COMMIT`, written by the workflow |
| `railway` | `backend/Dockerfile`, `.railway/railway.ts` | Railway pre-deploy command | `RAILWAY_GIT_COMMIT_SHA` |
| `vercel` | root `vercel.json` (services), `.github/workflows/deploy.yml` with a database | in the deploy workflow, before deploying | `VERCEL_GIT_COMMIT_SHA` |

Every project also reads its own `<PREFIX>COMMIT` first. With a visor, `frontend/vercel.json`
deploys it to Vercel; with `vercel`, visor and API share one project and one domain (`/api`), so
there is no CORS anywhere. Railway uses `.railway/railway.ts` (Infrastructure as Code) because
its `railway.json`/`railway.toml` format is deprecated and stops being read on 2026-12-01.

## Manual steps per target

Generating and checking a project needs no account. Deploying it needs these one-time steps; the
generated project's README ("Deploy") repeats the ones that apply, with its own names filled in.
Nothing in the template creates cloud resources.

- **Logfire** (all targets): create a project; a write token as `LOGFIRE_TOKEN` on the API's
  platform; a read token in `~/.config/<slug>/logfire-read-token` for `obs status`; for browser
  errors, a frontend application token as `VITE_LOGFIRE_TOKEN` in Vercel.
- **Neon** (with a database): a project in an EU region (`aws-eu-central-1`); the direct connection
  string for Render, Railway, FastAPI Cloud and migrations; the pooled one (`-pooler`) for Vercel.
- **Render**: New → Blueprint → the repository; set `DATABASE_URL` and `LOGFIRE_TOKEN` when asked.
- **FastAPI Cloud**: `fastapi login`, a first `fastapi deploy` from `backend/`, `fastapi cloud
  setup-ci --secrets-only` (GitHub secrets `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`), and
  `fastapi cloud env set` for `DATABASE_URL`, `LOGFIRE_TOKEN` and `<PREFIX>ENVIRONMENT`.
- **Railway**: `npm install --prefix .railway`, `railway link`, `railway config apply`; then
  `DATABASE_URL`, `LOGFIRE_TOKEN`, a public domain and "Wait for CI" in the dashboard.
- **Vercel** (visor, or `vercel` target): import the repository (root `frontend` for the visor
  alone, the repository root for the `vercel` target); environment variables `LOGFIRE_TOKEN`,
  `VITE_LOGFIRE_TOKEN` and, for `vercel` with a database, `DATABASE_URL` (pooled) plus the GitHub
  secrets of `deploy.yml` (`DATABASE_URL` direct, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`).
  With a non-Vercel API, check the API URL in `frontend/vercel.json`.
- **GitHub**: protect `main` with the required checks `Backend` and `Frontend`, and allow auto-merge.

## Update a project

Copier remembers the answers in the project's `.copier-answers.yml`. When the template improves:

```bash
cd my-project
git status                      # must be clean
copier update --defaults        # latest tagged release of the template
copier update --defaults --vcs-ref=HEAD   # or the template's latest commit
make setup && make check
```

Copier merges the template's changes with yours; conflicts appear as inline markers. Changing an
answer is also an update: `copier update --defaults --data api_deploy=railway`.

## Working on the template

The template lives in `template/` (`_subdirectory`); files ending in `.jinja` are rendered, and
names like `{% if with_frontend %}frontend{% endif %}` make whole files or folders conditional.

```bash
scripts/check-combination.sh /tmp/fsb-a                                  # defaults: make setup + make check
scripts/check-combination.sh /tmp/fsb-b --data api_deploy=railway --data type_checker=ty
scripts/check-update.sh /tmp/fsb-update                                  # copier update applies cleanly
```

The CI (`.github/workflows/ci.yml`) runs five combinations that cover every value of every option,
plus the update check. Agents working on the template read [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE). It covers the template itself; projects generated from it are yours to license as you wish.
