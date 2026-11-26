# full-stack-blueprint

A Copier template that generates a web project: FastAPI + asyncpg API, optional Vite + React
visor, optional PostgreSQL, and the deploy files of one target (Render, FastAPI Cloud, Railway or
Vercel). People start with the [README](README.md); this file is for coding agents working on or
with the template. Everything here is in English: code, docs, commit messages and pull requests.

**Design principle.** The template is built for development led by coding agents: the developer
directs and an agent such as Claude Code writes most of the code. Keep every change in that spirit:
explicit code an agent can read and verify over abstraction that saves a person typing (hence
asyncpg and plain SQL migrations, no ORM), commands that never prompt and end with a reliable exit
code, and contracts the CI checks (types, OpenAPI schema, generated client). The README section
"Built for development with coding agents" explains each choice.

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
  symlink to `template/.agents/skills` (`_preserve_symlinks`). Next to the project's own skills,
  `template/.agents/skills/` holds relative symlinks to skills that dependencies ship
  (`../../backend/.venv/lib/python3.14/site-packages/<package>/.agents/skills/<name>`), broken
  until `make setup`; the generated `scripts/check-skills.sh` (in `make check`) checks them.
- `scripts/check-combination.sh`: generates a project from the working tree and runs its
  `make setup` and `make check`. `scripts/check-update.sh`: checks that `copier update` applies a
  template change cleanly. `scripts/check-name-lengths.sh`: generates the backend for every
  package-name length (1 to 58) and runs ruff on all of them.
  `scripts/check-project-metadata.py` checks custom package names and the generated project metadata.
  `scripts/check-commit-style.py` checks both styles, saved answers, switching styles and updates
  from v0.10.0 (before the option); run it when changing commit guidance or the question.
- `.github/dependabot.yml`: weekly updates of the actions this repository's CI uses.
- `.github/workflows/ci.yml`: five combinations that cover every value of every option, the
  name-length check and the update check.
- `.github/workflows/release.yml` and `.github/release.yml`: at every pushed tag, publish the
  GitHub Release; its notes open with the tag's message and list the pull requests merged since
  the previous version.
- `.github/workflows/update-example.yml` and `scripts/update-example.sh`: at every pushed tag,
  update the example project the README links to and open a pull request there. Nothing to do by
  hand; the workflow's first comment explains its token.
- `.agents/skills/`: this repository's skills (`.claude/skills` links here).
  `.claude/settings.json` turns off Claude Code plugins this repository does not use.

## Rules for changing the template

- **Generated code must pass its own checks** for every combination: ruff format and lint, pyright
  and ty, pytest, oxfmt, oxlint, tsc, Vitest, build, Playwright. Watch Jinja whitespace
  (`{%- … %}` / `{% … -%}`) and line length: a long project name must not push a rendered line past
  100 characters (the CI has a combination with the longest name, 58 characters, the limit in
  `copier.yml`). Any length up to it matters too: ruff format rewraps a line just over 100
  characters when it fits once wrapped (the CI's name-length check tries them all). Prefer code
  whose line length does not depend on answers: an f-string over a constant such as `PREFIX`
  instead of the answer written into the line. oxfmt rewraps the visor's HTML as well, and joins a
  pre-wrapped element back when it fits: an HTML line that must hold an answer goes after a
  `<!-- prettier-ignore -->` comment, as in `index.html` (the CI has a long description).
- **Before a pull request**, run `scripts/check-combination.sh` for the combinations your change
  touches (at least the defaults), `scripts/check-update.sh` when you change file layout, and
  `scripts/check-name-lengths.sh` when you change a Python line that contains an answer.
  They take a few minutes each: run them in the background, once, at the end.
- **Library skills.** Link a skill a dependency ships (a relative symlink as above; a
  conditional name such as `{% if agent == 'x' %}name{% endif %}` works) only when its whole
  purpose fits every project that gets the link: not `logfire-setup`, `logfire-infrastructure`
  or `migrating-*`. Where its advice differs from the project's conventions, name the difference
  in the generated `AGENTS.md` ("Library skills are generic; this file wins"). Skills that
  live only in other repositories are listed in the generated README, never copied or fetched.
- **A new option or value** goes into at least one row of the CI matrix and into the README tables.
- **Nothing from any particular project** (domain names, data, people) enters the template.
- **Versions.** Python dependencies are lower bounds in `pyproject.toml.jinja`; the visor's are
  caret ranges except `oxfmt` (exact: beta formatter), `oxlint-tsgolint` (tilde: its version
  follows TypeScript's, 7.0.x with TypeScript 7.0) and `openapi-typescript`, run with `npx` at
  an exact version because it needs TypeScript 5's compiler API and the project uses TypeScript 7.
  Generated projects only install releases that are at least 7 days old (uv `exclude-newer`, npm
  `min-release-age`, Dependabot `cooldown`): a new lower bound or range must name a version
  published at least a week ago, or `make setup` cannot lock.
  GitHub Actions are pinned to a commit with the release in a comment (`uses: owner/action@<sha>
  # vX.Y.Z`), here and in the generated workflows. Dependabot updates this repository's CI
  (`.github/dependabot.yml`); make the same change in `template/.github/workflows/*.jinja`.
  Check the current docs of a platform before changing its deploy files; Railway's
  `railway.json` is deprecated (cutoff 2026-12-01), hence `.railway/railway.ts`.
- **Defaults that will change**: `type_checker` becomes `ty` at ty 1.0; `api_deploy` becomes
  `fastapi_cloud` when it has an EU region, a Dockerfile or pre-start command, rollbacks and
  usage-based billing. Each is a one-line change in `copier.yml` plus the README section.
  Two versions are held back: Python 3.15 until every deploy target runs it (Vercel's Python
  runtime, FastAPI Cloud) and PostgreSQL 19 until its first minor release and Neon offer it. The
  same README section lists where each version is written. openapi-typescript (maintenance mode)
  gives way to openapi-typesafe at its 1.0; the README section says how.
- **Pull requests**: small, one task each, a description with what, why, what to review and which
  checks ran; `gh pr merge --squash --auto` once complete (if the CI already passed, `--auto`
  refuses with "clean status": use `gh pr merge --squash`).
- **Releases** are annotated git tags (`vX.Y.Z`) on main, pushed after the merge: `copier update`
  takes the latest one by default, and the push publishes the release notes and updates the
  example. The tag's message opens the notes: one or two sentences on what changes for a project
  that updates, naming any new default it would take and the `--data` that keeps the old behavior.
