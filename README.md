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

- **API** (`backend/`): Python 3.14 with uv and uv_build, FastAPI, asyncpg without an ORM and a
  small packaged SQL migration runner (idempotent, PostgreSQL advisory lock, checksums),
  pydantic-settings, a Typer CLI (`migrate`, `openapi`, `obs status`), Logfire (works without a
  token), pytest against a real PostgreSQL, ruff, and pyright or ty.
- **Visor** (`frontend/`, optional): Vite 8, React 19, TypeScript 7, a client typed from the API's
  OpenAPI schema (`openapi-typescript` + `openapi-fetch`), oxlint, oxfmt (exact version), Vitest,
  Playwright, `@pydantic/logfire-browser` and Vercel Web Analytics.
- **Database** (optional): PostgreSQL 18 in docker-compose for development; Neon in production.
- **Deploy**: the API on Render (default), FastAPI Cloud, Railway or Vercel; the visor on Vercel.
  Only the chosen target's files are generated, in an EU region wherever the platform has one.
- **Repository**: a CI that skips the half a pull request does not touch and fails when the
  OpenAPI schema or the generated types are stale, grouped Dependabot updates, a 7-day wait before
  any new release is installed (Dependabot, uv, npm), VS Code settings that match the checks.

## Create your project, step by step

This walk-through takes you from an empty computer to a project that runs on your machine, lives
in its own GitHub repository and passes all its checks. The first time takes about half an hour,
mostly installing tools. You need no cloud account until you deploy.

### 1. Install the tools (once per computer)

- **git**, to keep the history of your code. macOS: `xcode-select --install` (it also brings
  `make`). Ubuntu/Debian: `sudo apt install git make`. Others: https://git-scm.com/downloads.
- **uv** 0.9.17 or newer, which runs Python and installs its packages. It downloads the right
  Python by itself, so you do not install Python separately:
  `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`).
- **Copier**, which generates the project from this template: `uv tool install copier`.
- **Node 24 LTS** (it brings npm 11.10 or newer), for the visor: https://nodejs.org (or
  `brew install node@24`, or `nvm install 24`). Not needed for a project without a visor.
- **Docker Desktop**, which runs the local PostgreSQL: https://docs.docker.com/get-docker/. Start
  it once after installing. Not needed for a project without a database.
- **GitHub CLI** (optional), to create the repository from the terminal: `brew install gh` or
  https://cli.github.com, then `gh auth login`.
- **A coding agent** (recommended), such as [Claude Code](https://claude.com/claude-code), Codex or
  Cursor: the template is made for working with one.

On Windows, install [WSL 2](https://learn.microsoft.com/windows/wsl/install) with Ubuntu, turn on
Docker Desktop's WSL 2 integration, and run every command of this guide inside Ubuntu: the
`Makefile` and the scripts need bash.

To see that everything is in place: `git --version`, `uv --version`, `copier --version`,
`node --version` and `docker info` should each print a version or a status, not an error.

### 2. Decide your answers

Copier asks one question per option, and every question has a default (the table in
[Options and defaults](#options-and-defaults) lists them all). Decide these before you start:

- **`project_name`**, the readable name, such as `Bus Stops`. The short names (`bus-stops` for the
  repository and commands, `bus_stops` for the Python package) are derived from it.
- **`github_repo`**, the repository you will create in step 4, as `your-user/bus-stops`. It does
  not need to exist yet.
- **`with_frontend`** and **`with_database`**: keep both (the default) unless you want an API
  without a visor or without PostgreSQL.
- **`api_deploy`**: where the API will run in production; Render unless you prefer another. You can
  change any answer later (see [Update a project](#update-a-project)).

### 3. Generate the project

From the folder where you keep your projects:

```bash
copier copy gh:ebotiab/full-stack-blueprint bus-stops
```

Copier asks each question with its default: press Enter to keep it. To skip the questions (what
agents do), take the defaults and override what you need:

```bash
copier copy --defaults \
  --data project_name="Bus Stops" \
  --data github_repo=your-user/bus-stops \
  gh:ebotiab/full-stack-blueprint bus-stops
```

or put the answers in a file: `copier copy --defaults --data-file answers.yml gh:ebotiab/full-stack-blueprint bus-stops`.
The template has no `_tasks`, so `--trust` is never needed.

### 4. Put it in git and on GitHub

```bash
cd bus-stops
git init -b main
git add -A
git commit -m "Generate from full-stack-blueprint"
```

With the GitHub CLI, one command creates the repository and uploads the code:

```bash
gh repo create your-user/bus-stops --private --source . --push
```

Without it, create an empty repository at https://github.com/new (add no README, `.gitignore` or
license: the project brings its own files), then:

```bash
git remote add origin https://github.com/your-user/bus-stops.git
git push -u origin main
```

### 5. Install and check everything

```bash
make doctor   # checks the tools and says how to fix whatever is missing
make setup    # dependencies, PostgreSQL, migrations, API schema and types
make check    # everything the CI runs: format, lint, types, tests, build, browser tests
```

Each command ends with a summary, one line per step: `ok` or `FAIL`. The first `make check` takes a
few minutes. When it ends with "All N steps passed.", save what `make setup` generated (lockfiles,
API schema and types):

```bash
git add -A
git commit -m "Lockfiles and generated API types"
git push
```

### 6. Run it

```bash
make dev
```

The API answers under http://127.0.0.1:8000/api (try http://127.0.0.1:8000/api/healthz), its
interactive documentation is at http://127.0.0.1:8000/docs and the visor is at
http://127.0.0.1:5173. Ctrl-C stops everything.

### 7. Work with a coding agent

Open the project folder with your agent (for Claude Code, run `claude` inside it). It reads
`AGENTS.md`, which has the layout, the commands and the conventions, and the skills in
`.agents/skills/` for usual tasks such as changing the API. Ask for a change in plain words, for
example "add an endpoint that lists bus stops near a point, with its table and migration". The
conventions ask the agent to write tests, run `make check` and open one small pull request per
task, marked to merge itself as soon as the CI passes; you can review it before then.
[Built for development with coding agents](#built-for-development-with-coding-agents) explains
how the template supports this way of working.

### 8. Deploy, when you are ready

Follow the steps for your target in [Manual steps per target](#manual-steps-per-target): a few
one-time accounts and secrets, plus protecting `main` on GitHub so that pull requests merge only
when the CI passes. After that, merging into `main` deploys.

### If something fails

- **`make doctor` reports a problem**: run the fix it prints under the failed line, then run
  `make doctor` again.
- **The PostgreSQL port is taken** (another project uses 5434): generate with another port, such as
  `--data postgres_port=5544`, or follow the fix `make doctor` prints.
- **Docker is installed but nothing starts**: open Docker Desktop and wait until it says it is
  running.
- **uv or npm cannot find a version** that exists: the project only installs releases that are at
  least 7 days old, as a protection against compromised packages. Use a version that is a week old.
- **`make check` fails**: the summary names the step. Formatting is fixed by `make fmt`; stale API
  types by `make types`; for anything else, the output above the summary says what broke. If you
  work with an agent, give it the summary.

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
