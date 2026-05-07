#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

usage() {
  cat <<'USAGE'
Usage:
  import_all_insert_sql.sh

Reads DB connection settings from .env in the same directory.

Required env vars:
  - PGDATABASE
  - PGUSER
  - PGPASSWORD
  - PGHOST (for direct connection) OR CLOUDSQL_INSTANCE (for proxy)

Optional env vars:
  - PGPORT (default: 5432)
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "This script does not accept CLI arguments. Use .env variables only." >&2
  usage
  exit 1
fi

INSTANCE="${CLOUDSQL_INSTANCE:-${INSTANCE:-}}"
DB_HOST="${PGHOST:-${DB_HOST:-}}"
DATABASE="${PGDATABASE:-${DATABASE:-}}"
DB_USER="${PGUSER:-${DB_USER:-}}"
DB_PASSWORD="${PGPASSWORD:-${DB_PASSWORD:-}}"
LOCAL_PORT="${PGPORT:-${LOCAL_PORT:-5432}}"

if [[ -z "$DATABASE" || -z "$DB_USER" || -z "$DB_PASSWORD" ]]; then
  echo "Missing required database arguments (PGDATABASE/PGUSER/PGPASSWORD)." >&2
  usage
  exit 1
fi

if [[ -z "$INSTANCE" && -z "$DB_HOST" ]]; then
  echo "Missing connection target: set CLOUDSQL_INSTANCE or PGHOST." >&2
  usage
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql is not installed or not in PATH." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${PROXY_PID:-}" ]] && kill -0 "$PROXY_PID" 2>/dev/null; then
    kill "$PROXY_PID" >/dev/null 2>&1 || true
    wait "$PROXY_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [[ -n "$INSTANCE" ]]; then
  if ! command -v cloud-sql-proxy >/dev/null 2>&1; then
    echo "Error: cloud-sql-proxy is not installed or not in PATH." >&2
    exit 1
  fi

  LOG_FILE="$(mktemp)"
  cloud-sql-proxy --address 127.0.0.1 --port "$LOCAL_PORT" "$INSTANCE" >"$LOG_FILE" 2>&1 &
  PROXY_PID=$!

  for _ in {1..20}; do
    if grep -Eq "Ready for new connections|Listening on" "$LOG_FILE"; then
      break
    fi
    if ! kill -0 "$PROXY_PID" 2>/dev/null; then
      echo "Connection failed: Cloud SQL Proxy stopped unexpectedly." >&2
      cat "$LOG_FILE" >&2
      exit 1
    fi
    sleep 0.5
  done

  if ! grep -Eq "Ready for new connections|Listening on" "$LOG_FILE"; then
    echo "Connection failed: Cloud SQL Proxy did not become ready in time." >&2
    cat "$LOG_FILE" >&2
    exit 1
  fi

  DB_HOST="127.0.0.1"
fi

shopt -s nullglob
sql_files=("$SCRIPT_DIR"/insert_*.sql)
shopt -u nullglob

if [[ ${#sql_files[@]} -eq 0 ]]; then
  echo "No files found matching: $SCRIPT_DIR/insert_*.sql" >&2
  exit 1
fi

printf '%s\n' "Found ${#sql_files[@]} SQL file(s) to import."

files_failed=0
total_attempted=0
total_inserted=0
total_skipped=0

for sql_file in "${sql_files[@]}"; do
  printf '\n==> Importing %s\n' "$(basename "$sql_file")"

  line_count=$(wc -l < "$sql_file")
  if [[ "$line_count" -eq 0 ]]; then
    printf '   Done %s (empty file).\n' "$(basename "$sql_file")"
    continue
  fi

  file_attempted=0
  file_inserted=0
  file_skipped=0
  file_had_non_zero=0

  chunk_start=1
  while [[ $chunk_start -le $line_count ]]; do
    chunk_end=$((chunk_start + 999))
    if [[ $chunk_end -gt $line_count ]]; then
      chunk_end=$line_count
    fi

    chunk_file="$(mktemp)"
    err_log="$(mktemp)"
    out_log="$(mktemp)"
    sed -n "${chunk_start},${chunk_end}p" "$sql_file" > "$chunk_file"

    set +e
    PGPASSWORD="$DB_PASSWORD" psql \
      "host=$DB_HOST port=$LOCAL_PORT dbname=$DATABASE user=$DB_USER sslmode=disable connect_timeout=10" \
      -v ON_ERROR_STOP=0 \
      -f "$chunk_file" \
      2>"$err_log" \
      1>"$out_log"
    status=$?
    set -e

    if [[ $status -ne 0 ]]; then
      file_had_non_zero=1
    fi

    attempted_in_chunk=$((chunk_end - chunk_start + 1))
    inserted_in_chunk=$(grep -c '^INSERT 0 1$' "$out_log" || true)
    skipped_in_chunk=$(grep -c '^INSERT 0 0$' "$out_log" || true)

    file_attempted=$((file_attempted + attempted_in_chunk))
    file_inserted=$((file_inserted + inserted_in_chunk))
    file_skipped=$((file_skipped + skipped_in_chunk))
    total_attempted=$((total_attempted + attempted_in_chunk))
    total_inserted=$((total_inserted + inserted_in_chunk))
    total_skipped=$((total_skipped + skipped_in_chunk))

    printf '%s/%s\n' "$total_inserted" "$total_attempted"

    rm -f "$chunk_file" "$err_log" "$out_log"
    chunk_start=$((chunk_end + 1))
  done

  if [[ $file_had_non_zero -eq 1 ]]; then
    files_failed=$((files_failed + 1))
  fi

  printf '   File summary %s: inserted=%s skipped=%s attempted=%s\n' \
    "$(basename "$sql_file")" "$file_inserted" "$file_skipped" "$file_attempted"
done

printf '\nImport summary:\n'
printf '  Files processed: %s\n' "${#sql_files[@]}"
printf '  Files with psql non-zero exit: %s\n' "$files_failed"
printf '  Total inserted / attempted: %s/%s\n' "$total_inserted" "$total_attempted"
printf '  Total skipped (INSERT 0 0): %s\n' "$total_skipped"

if [[ $files_failed -gt 0 ]]; then
  exit 1
fi

exit 0
