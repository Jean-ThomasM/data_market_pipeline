#!/usr/bin/env bash
# Sync input from GCS and output to GCS

set -euo pipefail

BUCKET_NAME="n8n-input"
BASE_DIR="/home/christian_martiny/files"

INPUT_DEST_FILE="${BASE_DIR}/input/input.json"
INPUT_TMP_FILE="${BASE_DIR}/input/input.tmp.json"
INPUT_BUCKET_FILE="gs://${BUCKET_NAME}/files/input/input.json"

OUTPUT_SOURCE_FILE="${BASE_DIR}/output/output.json"
OUTPUT_BUCKET_FILE="gs://${BUCKET_NAME}/output.json"

GCLOUD_BIN="/usr/bin/gcloud"

# Download input.json from GCS
mkdir -p "$(dirname "${INPUT_DEST_FILE}")"
"${GCLOUD_BIN}" storage cp "${INPUT_BUCKET_FILE}" "${INPUT_TMP_FILE}"

# Atomic replace for input.json
mv "${INPUT_TMP_FILE}" "${INPUT_DEST_FILE}"

# Upload output.json to GCS if it exists
if [ -f "${OUTPUT_SOURCE_FILE}" ]; then
    "${GCLOUD_BIN}" storage cp "${OUTPUT_SOURCE_FILE}" "${OUTPUT_BUCKET_FILE}"
    echo "output.json uploaded to bucket"
else
    echo "output.json not found, upload skipped"
fi

echo "sync completed at $(date '+%Y-%m-%d %H:%M:%S')"
