---
name: new-project
description: Generate a new project from the full-stack-blueprint Copier template without prompts, get it to a passing `make check`, update an existing project with `copier update`, and list the manual deploy steps that remain for its target. Use it when asked to start, scaffold or bootstrap a project with this stack, or to bring a generated project up to date with the template.
---

# New project from full-stack-blueprint

The options and their defaults are in the README ("Options and defaults"); `copier.yml` has the
`help` of each. Ask the user only what the request does not settle and has no sensible default:
usually the project name, whether it needs the visor and the database, and the deploy target.

## Generate

1. Make sure Copier is installed: `uv tool install copier` (9.8 or newer, which `copier.yml`
   requires: it validates the derived names under `--defaults`, and a question without a default
   fails instead of hanging; every question here has one).
2. Generate without prompts, overriding only what differs from the defaults:

   ```bash
   copier copy --defaults \
     --data project_name="Bus Stops" \
     --data github_repo=owner/bus-stops \
     --data api_deploy=render \
     gh:ebotiab/full-stack-blueprint ~/path/bus-stops
   ```

   Use a local path to the template instead of `gh:…` when working from a checkout, and add
   `--vcs-ref HEAD` to use its latest commit instead of its latest tag. Never pass `--trust`:
   the template does not need it.
3. Commit the generated files before anything else (Copier's updates rely on git history):
   `git init -b main && git add -A && git commit -m "Generate from full-stack-blueprint"`.
4. `make doctor`. If it fails, it prints how to fix each missing tool; tell the user when a fix
   needs them (installing Docker, starting Docker Desktop).
5. `make setup`, then `make check` (a few minutes: run it in the background if you can). Both end
   with a summary; everything must say `ok`.
6. Commit what setup generated (`backend/uv.lock`, `frontend/package-lock.json`,
   `backend/openapi.json`, `frontend/src/api/schema.d.ts`).
7. If the user wants it on GitHub, create the repository (ask public or private), push, and tell
   them to protect `main` with the required checks `Backend` and `Frontend` and to allow auto-merge.

From here the project's own `AGENTS.md` and skills (`ship-a-change`, `change-the-api`) apply.

## Update an existing project

1. In the project, `git status` must be clean.
2. `copier update --defaults` (latest tagged template) or `copier update --defaults --vcs-ref=HEAD`
   (latest commit). To change an answer: add `--data key=value`.
3. Look for conflict markers (`git grep -nE '^(<<<<<<<|>>>>>>>)'`) and `*.rej` files; resolve them
   keeping the project's own changes.
4. `make setup && make check`, then open a pull request with the update.

## Manual steps that remain (tell the user; do not do them without their go-ahead)

Every target:

- **Logfire**: a project; a write token as `LOGFIRE_TOKEN` where the API runs; a read token in
  `~/.config/<slug>/logfire-read-token` for `obs status`; with a visor, a frontend application
  token as `VITE_LOGFIRE_TOKEN` in Vercel.
- **Neon** (with a database): a project in an EU region; the direct connection string as
  `DATABASE_URL` (the pooled `-pooler` one on Vercel).
- **GitHub**: branch protection with `Backend` and `Frontend`, auto-merge allowed.

Per `api_deploy`:

- `render`: Render → New → Blueprint → the repository; fill `DATABASE_URL` and `LOGFIRE_TOKEN`.
- `fastapi_cloud`: in `backend/`, `uv run fastapi login`, a first `uv run fastapi deploy`,
  `uv run fastapi cloud setup-ci --secrets-only`, and `uv run fastapi cloud env set --secret …` for
  `DATABASE_URL` and `LOGFIRE_TOKEN` (plus `<PREFIX>ENVIRONMENT=production`).
- `railway`: `npm install --prefix .railway`, `railway login`, `railway link`,
  `railway config plan`, `railway config apply`; in the dashboard: `DATABASE_URL`,
  `LOGFIRE_TOKEN`, a public domain, "Wait for CI".
- `vercel`: import the repository (root directory = repository root); `DATABASE_URL` (pooled) and
  `LOGFIRE_TOKEN` as environment variables; with a database also the GitHub secrets of
  `deploy.yml`: `DATABASE_URL` (direct), `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.

With a visor and a non-Vercel API: import the repository in Vercel with root directory `frontend`,
and check the API URL in `frontend/vercel.json` once the API has its real address.
