#!/usr/bin/env bash
# Generate a project from this template (working tree, uncommitted changes included) and run its
# own `make setup` and `make check`. Used by the template's CI and by hand:
#
#   scripts/check-combination.sh <output-dir> [copier --data arguments...]
#   scripts/check-combination.sh /tmp/fsb-default
#   scripts/check-combination.sh /tmp/fsb-railway --data api_deploy=railway --data type_checker=ty
#
# The output directory must not exist. The generated project is committed in a fresh git
# repository first, as a person would, so `copier update` can be tried on it afterwards.
#
# When the script ends, passed or failed, it removes what `make setup` started in Docker
# (PostgreSQL, Mailpit) together with its data: the project is throwaway, and a container left
# running blocks the next run of a combination with the same project name. The project's files
# stay; `make db-up` in it starts an empty database again (then `make setup` migrates it).
#
# The generated docker-compose.yml names its Compose project after the project (`name:`), and every
# checkout of a real project with that name shares it. This run uses its own, named after the
# output directory, so the `docker compose down --volumes` at the end never removes a real
# project's database: COMPOSE_PROJECT_NAME comes before `name:`, and make's commands inherit it.
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <output-dir> [--data key=value ...]" >&2
  exit 2
fi
out=$1
shift
template=$(cd "$(dirname "$0")/.." && pwd)

if [ -e "$out" ]; then
  echo "$out already exists: pick a new directory." >&2
  exit 2
fi

echo "==> copier copy --defaults $* → $out"
copier copy --defaults --vcs-ref HEAD "$@" "$template" "$out"

cd "$out"
project=$(pwd)
COMPOSE_PROJECT_NAME="fsb-check-$(basename "$project" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9_\n-' '-')"
export COMPOSE_PROJECT_NAME
stop_docker() {
  if [ -f "$project/docker-compose.yml" ]; then
    echo "==> docker compose down --volumes"
    (cd "$project" && docker compose down --volumes --remove-orphans) || true
  fi
}
trap stop_docker EXIT

git init -q -b main
git add -A
git -c user.name=template-ci -c user.email=template-ci@example.invalid commit -qm "Generate from template"

echo "==> make setup"
make setup
echo "==> make check"
make check

# What setup generated (lockfiles, openapi.json, schema.d.ts) is committed too, as the project's
# AGENTS.md asks; then the worktree must be clean.
git add -A
git -c user.name=template-ci -c user.email=template-ci@example.invalid commit -qm "Lockfiles and generated API types" || true
if [ -n "$(git status --porcelain)" ]; then
  echo "make check left the worktree dirty:" >&2
  git status --short >&2
  exit 1
fi
echo "==> $out passed."
