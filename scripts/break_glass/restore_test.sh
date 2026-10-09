#!/usr/bin/env bash
# Restore test for the break-glass dump (Tasks#75, decision D3).
#
# Restores one dump folder (as downloaded from s3://sln-break-glass/dumps/...)
# into a throwaway Postgres 18 container, then checks each table: the restored
# row count must equal the number of rows the dump holds. It also shows the
# counts the dump job recorded in prod (row_counts.csv), which can differ by a
# few rows because they are read moments after the dump.
#
# Usage: scripts/break_glass/restore_test.sh <dump-folder>
# Needs: Docker. Touches nothing outside the container it starts.
set -euo pipefail

DIR=${1:?usage: restore_test.sh <dump-folder>}
DIR=$(cd "$DIR" && pwd)
# Git Bash on Windows: stop path conversion of container paths, mount a Windows path.
export MSYS_NO_PATHCONV=1
MOUNT=$DIR
if command -v cygpath >/dev/null 2>&1; then MOUNT=$(cygpath -w "$DIR"); fi
IMAGE=${RESTORE_TEST_IMAGE:-postgres:18.6}
NAME=sln-break-glass-restore-test-$$

for f in sln_own_tables.dump SHA256SUMS; do
  [ -f "$DIR/$f" ] || { echo "missing $DIR/$f" >&2; exit 1; }
done

(cd "$DIR" && sha256sum -c SHA256SUMS)

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e POSTGRES_PASSWORD=restore-test \
  -v "$MOUNT:/dump:ro" "$IMAGE" >/dev/null
for _ in $(seq 1 60); do
  docker exec "$NAME" pg_isready -U postgres -q && break
  sleep 1
done
docker exec "$NAME" pg_isready -U postgres -q
docker exec "$NAME" createdb -U postgres restore_check

# Foreign keys to LL tables that are not in the dump (api_launch, auth_permission,
# django_content_type and others) cannot be created here, so leave every FK out.
docker exec "$NAME" sh -c \
  'pg_restore -l /dump/sln_own_tables.dump | grep -v " FK CONSTRAINT " > /tmp/toc.txt'
docker exec "$NAME" pg_restore -U postgres -d restore_check -L /tmp/toc.txt \
  --no-owner --no-acl --exit-on-error /dump/sln_own_tables.dump

# Rows per table as held in the dump: lines between "COPY public.<t> ..." and "\.".
docker exec "$NAME" sh -c 'pg_restore -f - --data-only /dump/sln_own_tables.dump |
  awk "/^COPY / {t=\$2; sub(/^public\\./, \"\", t); n=0; next}
       /^\\\\\\.\$/ {if (t != \"\") print t \",\" n; t=\"\"; next}
       t != \"\" {n++}"' > "$DIR/.dump_rows.csv"

FAIL=0
printf '%-40s %10s %10s %10s\n' table in_dump restored prod_count
while IFS=, read -r table rows; do
  restored=$(docker exec "$NAME" psql -U postgres -d restore_check -XAt \
    -c "SELECT count(*) FROM public.\"$table\"")
  prod=$(grep -m1 "^$table," "$DIR/row_counts.csv" 2>/dev/null | cut -d, -f2 || true)
  mark=""
  if [ "$restored" != "$rows" ]; then mark="  MISMATCH"; FAIL=1; fi
  printf '%-40s %10s %10s %10s%s\n' "$table" "$rows" "$restored" "${prod:--}" "$mark"
done < "$DIR/.dump_rows.csv"
rm -f "$DIR/.dump_rows.csv"

for csv in launch_flags.csv event_flags.csv; do
  [ -f "$DIR/$csv" ] && echo "$csv: $(($(wc -l < "$DIR/$csv") - 1)) rows"
done

if [ "$FAIL" -ne 0 ]; then
  echo "RESTORE TEST FAILED: restored counts differ from the dump" >&2
  exit 1
fi
echo "RESTORE TEST PASSED"
