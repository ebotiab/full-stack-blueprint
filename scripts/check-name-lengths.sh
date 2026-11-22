#!/usr/bin/env bash
# Generate the backend for every package-name length the template accepts (1 to 58 characters)
# and run the generated project's own ruff on all of them (`ruff format --check`, `ruff check`).
# It also checks that copier rejects a package name that is too long or a standard-library module.
# Used by the template's CI and by hand:
#
#   scripts/check-name-lengths.sh <output-dir>
#
# The names end up in Python lines (imports, strings). ruff format rewraps a line just over 100
# characters only when it fits once wrapped, so a name can break the generated project for a band
# of lengths that the CI's combinations, with one name each, step over. Two combinations cover the
# Python files that depend on the options: Vercel with a database and sign-in (main.py, db/,
# auth/) and Render without a database, with OIDC sign-in. It takes a minute or two; no Docker,
# no npm.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: $0 <output-dir>" >&2
  exit 2
fi
out=$1
template=$(cd "$(dirname "$0")/.." && pwd)
max=58 # the limit in copier.yml (package_name)

if [ -e "$out" ]; then
  echo "$out already exists: pick a new directory." >&2
  exit 2
fi
mkdir -p "$out"

# The project name of each length: its slug, package and prefix derive from it with the same
# length. It starts with "name" so that no short one is a standard-library module ("abc", "re").
words=name-length-check-name-length-check-name-length-check-name-length-check-name-length
name_of_length() {
  local name=${words:0:$1}
  case $name in *-) name=${name%-}x ;; esac
  echo "$name"
}

# render <combination> <length>
render() {
  local options
  case $1 in
    vercel-db) options=(--data api_deploy=vercel --data auth=sessions --data email=smtp --data jobs=postgres) ;;
    render-nodb) options=(--data with_database=false --data auth=oidc) ;;
  esac
  # PYTHONWARNINGS: one "dirty template" warning per project would bury the output.
  PYTHONWARNINGS=ignore copier copy --quiet --defaults --vcs-ref HEAD --data with_frontend=false \
    "${options[@]}" --data "project_name=$(name_of_length "$2")" "$template" "$out/$1-$2"
}
export -f render name_of_length
export template out words

echo "==> copier copy, lengths 1 to $max, two combinations → $out"
for n in $(seq 1 "$max"); do
  echo "vercel-db $n"
  echo "render-nodb $n"
done | xargs -P 4 -n 2 bash -c 'render "$@"' _

echo "==> the generated project's ruff (uv sync in one of them)"
(cd "$out/render-nodb-$max/backend" && uv sync --quiet)
ruff=$out/render-nodb-$max/backend/.venv/bin/ruff

# Each project's own pyproject.toml applies to its files (ruff uses the closest configuration).
echo "==> ruff format --check and ruff check on all of them"
status=0
"$ruff" format --check --no-cache "$out"/*/backend || status=1
"$ruff" check --no-cache --output-format concise "$out"/*/backend || status=1
if [ "$status" -ne 0 ]; then
  echo "A name length breaks a generated line: the directory above says the combination and the" >&2
  echo "length. Write the line so its length does not depend on the name (e.g. an f-string over" >&2
  echo "a constant)." >&2
  exit 1
fi

echo "==> a name of $((max + 1)) characters is rejected"
if copier copy --quiet --defaults --vcs-ref HEAD --data "project_name=$(name_of_length $((max + 1)))" \
  "$template" "$out/rejected" >/dev/null 2>&1; then
  echo "copier accepted a package name of $((max + 1)) characters: see package_name in copier.yml." >&2
  exit 1
fi

echo "==> a standard-library module name is rejected (project \"Calendar\" → package calendar)"
output=$(copier copy --quiet --defaults --vcs-ref HEAD --data project_name=Calendar \
  "$template" "$out/stdlib" 2>&1) || true
if ! grep -q "standard library" <<<"$output"; then
  echo "$output" >&2
  echo "copier did not reject the package name calendar: see package_name in copier.yml." >&2
  exit 1
fi
echo "==> every length passed."
