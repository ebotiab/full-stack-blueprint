# full-stack-blueprint

A Copier template that generates a web project: FastAPI + asyncpg API, optional Vite + React
visor, optional PostgreSQL, and the deploy files of one target (Render, FastAPI Cloud, Railway or
Vercel). People start with the [README](README.md); this file is for coding agents working on or
with the template. Everything here is in English: code, docs, commit messages and pull requests.

## Using the template (generating or updating a project)

Follow the `new-project` skill (`.agents/skills/new-project/SKILL.md`): it covers generating
without prompts, the first `make setup` / `make check`, `copier update`, and the manual steps
that remain per deploy target. Never create services on Render, FastAPI Cloud, Railway, Vercel,
Neon or Logfire without the user's explicit go-ahead.

## Where things are

- `copier.yml`: the questions. Every one has a default and a `help`, so `copier copy --defaults`
  never prompts. No `_tasks` (so `--trust` is never needed): set-up lives in the generated `Makefile`.
- `template/`: the generated project (`_subdirectory`). `.jinja` files are rendered; a name such
  as `{% if with_database %}db{% endif %}` makes a file or folder conditional (directories never
  carry the `.jinja` suffix; use single quotes inside names). `template/.claude/skills` is a
  symlink to `template/.agents/skills` (`_preserve_symlinks`).
- `scripts/check-combination.sh`: generates a project from the working tree and runs its
  `make setup` and `make check`. `scripts/check-update.sh`: checks that `copier update` applies a
  template change cleanly.
- `.github/workflows/ci.yml`: five combinations that cover every value of every option, and the
  update check.
- `.agents/skills/`: this repository's skills (`.claude/skills` links here).
  `.claude/settings.json` turns off Claude Code plugins this repository does not use.

## Rules for changing the template

- **Generated code must pass its own checks** for every combination: ruff format and lint, pyright
  and ty, pytest, oxfmt, oxlint, tsc, Vitest, build, Playwright. Watch Jinja whitespace
  (`{%- … %}` / `{% … -%}`) and line length: a long project name must not push a rendered line past
  100 characters (the CI has a long-name combination). A mid-length name matters too: ruff format
  rewraps a line just over 100 characters when it fits once wrapped (the CI has a mid-length-name
  combination). Prefer code whose line length does not depend on answers.
- **Before a pull request**, run `scripts/check-combination.sh` for the combinations your change
  touches (at least the defaults), and `scripts/check-update.sh` when you change file layout.
  They take a few minutes each: run them in the background, once, at the end.
- **A new option or value** goes into at least one row of the CI matrix and into the README tables.
- **Nothing from any particular project** (domain names, data, people) enters the template.
- **Versions.** Python dependencies are lower bounds in `pyproject.toml.jinja`; the visor's are
  caret ranges except `oxfmt` (exact: beta formatter) and `openapi-typescript`, run with `npx` at
  an exact version because it needs TypeScript 5's compiler API and the project uses TypeScript 7.
  Check the current docs of a platform before changing its deploy files; Railway's
  `railway.json` is deprecated (cutoff 2026-12-01), hence `.railway/railway.ts`.
- **Defaults that will change**: `type_checker` becomes `ty` at ty 1.0; `api_deploy` becomes
  `fastapi_cloud` when it has an EU region, a Dockerfile or pre-start command, rollbacks and
  usage-based billing. Each is a one-line change in `copier.yml` plus the README section.
- **Pull requests**: small, one task each, a description with what, why, what to review and which
  checks ran; `gh pr merge --squash --auto` once complete. Releases are git tags (`vX.Y.Z`):
  `copier update` takes the latest tag by default.
