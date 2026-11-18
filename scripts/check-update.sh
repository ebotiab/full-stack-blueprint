#!/usr/bin/env bash
# Check that `copier update` applies cleanly: generate a project from the template's current
# commit, add a test change to a copy of the template, update the project to it and verify the
# change arrived with no conflicts. Needs only git and copier (no make setup).
#
#   scripts/check-update.sh <work-dir>
set -euo pipefail

if [ $# -ne 1 ] || [ -e "$1" ]; then
  echo "usage: $0 <work-dir that does not exist yet>" >&2
  exit 2
fi
work=$1
template=$(cd "$(dirname "$0")/.." && pwd)
git_id=(-c user.name=template-ci -c user.email=template-ci@example.invalid)

mkdir -p "$work"
# A copy of the template with its current state committed, so the test never touches the real one.
rsync -a --exclude .git --exclude node_modules --exclude .venv "$template/" "$work/template/"
git -C "$work/template" init -q -b main
git -C "$work/template" add -A
git "${git_id[@]}" -C "$work/template" commit -qm "Template under test" --allow-empty

copier copy --defaults --vcs-ref HEAD "$work/template" "$work/project"
git -C "$work/project" init -q -b main
git -C "$work/project" add -A
git "${git_id[@]}" -C "$work/project" commit -qm "Generate from template"

# The test change: a new line in a file every project has.
marker="Template update test line."
printf '\n%s\n' "$marker" >> "$work/template/template/AGENTS.md.jinja"
git "${git_id[@]}" -C "$work/template" commit -qam "Test change"

(cd "$work/project" && copier update --defaults --vcs-ref HEAD --conflict inline)

cd "$work/project"
if ! grep -qF "$marker" AGENTS.md; then
  echo "The test change did not reach the project." >&2
  exit 1
fi
if git grep -nE '^(<<<<<<<|>>>>>>>)' -- . ':!*.lock' || find . -name '*.rej' -not -path './.git/*' | grep -q .; then
  echo "copier update left conflicts." >&2
  exit 1
fi
echo "==> copier update applied cleanly:"
git status --short
