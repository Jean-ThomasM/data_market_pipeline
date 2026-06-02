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
  check_gcp_cloudsql_connection.sh

Environment variables supported:
  CLOUDSQL_INSTANCE, PGHOST, PGDATABASE, PGUSER, PGPASSWORD, PGPORT

Behavior:
  - If CLOUDSQL_INSTANCE is set, connection uses Cloud SQL Auth Proxy.
  - Otherwise, connection uses PGHOST/PGPORT directly.

Required tools:
  - psql
  - cloud-sql-proxy (only when using --instance)
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

if [[ -z "$INSTANCE" && -z "$DB_HOST" ]]; then
  echo "Missing connection target: set CLOUDSQL_INSTANCE or PGHOST." >&2
  usage
  exit 1
fi

if [[ -z "$DATABASE" || -z "$DB_USER" || -z "$DB_PASSWORD" ]]; then
  echo "Missing required database arguments (database/user/password)." >&2
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

RESULT="$(PGPASSWORD="$DB_PASSWORD" psql \
  "host=$DB_HOST port=$LOCAL_PORT dbname=$DATABASE user=$DB_USER sslmode=disable connect_timeout=5" \
  -tAc "SELECT 1;")"

if [[ "$RESULT" == "1" ]]; then
  if [[ -n "$INSTANCE" ]]; then
    echo "Cloud SQL connection OK via proxy (${INSTANCE}, db=${DATABASE}, user=${DB_USER})."
  else
    echo "Cloud SQL connection OK via host (${DB_HOST}:${LOCAL_PORT}, db=${DATABASE}, user=${DB_USER})."
  fi
  exit 0
fi

echo "Connection failed: unexpected SQL response: ${RESULT}" >&2
exit 1
