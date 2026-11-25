#!/usr/bin/env bash
# Decide which half of the CI a list of changed files can affect.
#
# Reads one path per line on stdin and writes `backend=true|false` and `frontend=true|false`, the
# $GITHUB_OUTPUT format. A half is skipped only when no file in the list can change its result;
# anything not classified here runs both.
#
#   git diff --name-only --no-renames HEAD^1 HEAD | .github/scripts/what-changed.sh
#
# Why each rule:
# - make check-backend checks AGENTS.md, its CLAUDE.md import, .claude/skills and .agents/.
# - Other root Markdown files, docs/, .vscode/ and the rest of .claude/ can skip both halves.
# - backend/openapi.json is the contract: the backend checks it matches the code and the visor
#   checks its generated types match it, so it runs both.
# If you add a check that reads a file from the other half, add a rule here.
set -euo pipefail

backend=false
frontend=false
files=0

while IFS= read -r path; do
  [ -z "$path" ] && continue
  files=$((files + 1))
  case "$path" in
    AGENTS.md | CLAUDE.md | .claude/skills | .claude/skills/* | .agents/*) backend=true ;;
    docs/* | .vscode/* | .claude/*) ;;
    backend/openapi.json) backend=true; frontend=true ;;
    backend/*) backend=true ;;
    frontend/*) frontend=true ;;
    */*) backend=true; frontend=true ;;
    *.md) ;;
    *) backend=true; frontend=true ;;
  esac
done

# With no files there is nothing that justifies skipping a half.
if [ "$files" -eq 0 ]; then
  backend=true
  frontend=true
fi

echo "backend=$backend"
echo "frontend=$frontend"
