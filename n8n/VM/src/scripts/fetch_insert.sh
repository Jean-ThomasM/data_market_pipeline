#!/usr/bin/env bash
# Fetch insert.sql and input.json from GCS to VM

set -euo pipefail

BUCKET_NAME="n8n-input"
BASE_DIR="/home/christian_martiny/files"

INSERT_DEST_FILE="${BASE_DIR}/insert.sql"
INSERT_TMP_FILE="${BASE_DIR}/insert.tmp.sql"
INSERT_BUCKET_FILE="gs://${BUCKET_NAME}/files/insert.sql"

INPUT_DEST_FILE="${BASE_DIR}/input/input.json"
INPUT_TMP_FILE="${BASE_DIR}/input/input.tmp.json"
INPUT_BUCKET_FILE="gs://${BUCKET_NAME}/files/input/input.json"

GCLOUD_BIN="/usr/bin/gcloud"

mkdir -p "${BASE_DIR}" "$(dirname "${INPUT_DEST_FILE}")"

# Download insert.sql from GCS and atomic replace
"${GCLOUD_BIN}" storage cp "${INSERT_BUCKET_FILE}" "${INSERT_TMP_FILE}"
mv "${INSERT_TMP_FILE}" "${INSERT_DEST_FILE}"
echo "insert.sql updated"

# Download input.json from GCS and atomic replace
"${GCLOUD_BIN}" storage cp "${INPUT_BUCKET_FILE}" "${INPUT_TMP_FILE}"
mv "${INPUT_TMP_FILE}" "${INPUT_DEST_FILE}"
echo "input.json updated"

echo "fetch completed at $(date '+%Y-%m-%d %H:%M:%S')"
