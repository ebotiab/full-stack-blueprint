#!/usr/bin/env bash
# Exercise the same Git worktree names, Makefile URLs and managed .env files that agents use.
# Runs with only git, Copier and make. The database itself is covered by the combination jobs.
set -euo pipefail
if [ $# -ne 1 ] || [ -e "$1" ]; then
  echo "usage: $0 <new-work-dir>" >&2
  exit 2
fi
mkdir -p "$1"
work=$(cd "$1" && pwd)
template=$(cd "$(dirname "$0")/.." && pwd)
project=$work/main
copier copy --quiet --defaults --vcs-ref HEAD --data project_slug=wt-feature-a-test "$template" "$project"
git -C "$project" init -q -b main
git -C "$project" add -A
git -C "$project" -c user.name=template-ci -c user.email=ci@example.invalid commit -qm generated

long=worktree-name-with-a-common-prefix-longer-than-fifty-five-characters
names=(main feature-a feature_a feature-a-test "${long}-one" "${long}-two")
for name in "${names[@]}"; do
  checkout=$work/$name
  if [ "$name" != main ]; then git -C "$project" worktree add -q --detach "$checkout"; fi
  dev=$(bash "$checkout/scripts/db-name.sh")
  url=$(make -s -C "$checkout" -f Makefile -f - print-test-url <<'MAKE'
print-test-url:
	@printf '%s\n' '$(TEST_DATABASE_URL)'
MAKE
)
  test_db=${url##*/}
  if [ "$name" = main ]; then [ "$dev" = wt_feature_a_test ]; fi
  [ "$test_db" = "$dev-test" ]
  [ "${#test_db}" -le 63 ]
  printf '%s\n' "$dev" "$test_db" >> "$work/names"
done
if [ -n "$(sort "$work/names" | uniq -d)" ]; then
  echo "Two development or test databases have the same name:" >&2
  cat "$work/names" >&2
  exit 1
fi

# Simulate already-provisioned containers to exercise just the .env upgrade path without Docker.
mkdir "$work/bin"
cat > "$work/bin/docker" <<'STUB'
#!/usr/bin/env bash
case "$*" in
  'compose up '*) exit 0 ;;
  'compose exec -T postgres psql '*) cat >/dev/null; echo 1 ;;
  *) exit 1 ;;
esac
STUB
chmod +x "$work/bin/docker"
export PATH="$work/bin:$PATH"
cd "$work/feature-a"
pg=postgresql://wt_feature_a_test:wt_feature_a_test@localhost:5434
key=WT_FEATURE_A_TEST_DATABASE_URL
marker="# This git worktree's own database (make db-up, scripts/db-name.sh)."
printf '%s\n' 'KEEP=value' "$marker" "$key=$pg/wt_feature_a" > backend/.env
make -s db-up
dev=$(bash scripts/db-name.sh)
printf '%s\n' 'KEEP=value' "$marker" "$key=$pg/$dev" > "$work/expected"
cmp "$work/expected" backend/.env
make -s db-up
cmp "$work/expected" backend/.env
printf '%s\n' "$marker" "$key=postgresql://custom/explicit" > backend/.env
cp backend/.env "$work/expected"
make -s db-up
cmp "$work/expected" backend/.env
echo "Worktree database names are disjoint and existing settings are preserved."
