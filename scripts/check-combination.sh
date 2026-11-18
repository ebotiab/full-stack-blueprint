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
