#!/usr/bin/env bash
# Bring a checkout of the example project (the one the README links to) up to date with this
# template: `copier update` to a version of the template (the workflow passes the release's tag;
# the default is the latest commit), then regenerate what `make setup` generates and the project
# commits (lockfiles, OpenAPI schema, API types).
#
#   scripts/update-example.sh <checkout-of-the-example> [template-ref]
#
# The checkout must be clean. The script changes files and commits nothing: the caller looks at
# `git status` and decides what to do (.github/workflows/update-example.yml opens a pull request).
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <checkout-of-the-example> [template-ref]" >&2
  exit 2
fi
project=$1
ref=${2:-HEAD}
# The example takes every default answer except one: it shows the optional sign-in, which projects
# do not get by default. Passed on every update so that the answer cannot drift. ui is passed too:
# the example recorded `css` before `tailwind` became the default, and a recorded answer wins.
example_data=(--data auth=sessions --data ui=tailwind)

cd "$project"
if [ -n "$(git status --porcelain)" ]; then
  echo "$project has uncommitted changes: commit or discard them first." >&2
  exit 2
fi

echo "==> copier update --defaults --vcs-ref=$ref ${example_data[*]}"
copier update --defaults --vcs-ref="$ref" "${example_data[@]}"

# Copier leaves a conflict as inline markers or as a .rej file. Nobody edits the example by hand,
# so either one means the update needs a person.
if git grep -nE '^(<<<<<<<|>>>>>>>) ' -- . >/dev/null \
  || [ -n "$(git ls-files --others --exclude-standard -- '*.rej')" ]; then
  echo "copier update left conflicts:" >&2
  git status --short >&2
  exit 1
fi

if [ -z "$(git status --porcelain)" ]; then
  echo "==> The example is already up to date."
  exit 0
fi

echo "==> Lockfiles and generated API files"
(cd backend && uv sync)
(cd frontend && npm install)
make types

echo "==> Changed:"
git status --short
