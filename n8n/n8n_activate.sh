#!/bin/bash
set -euo pipefail

N8N_URL="${1:-https://n8n-dev-822083335202.europe-west1.run.app}"
WORKFLOW_ID="e1b2c3d4-5a6b-7c8d-9e0f-a1b2c3d4e5f6"
OWNER_EMAIL="admin@datamarket.local"
OWNER_PASSWORD="DataMarket2024!"

echo "=== Setting up owner ==="
OWNER_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$N8N_URL/rest/owner/setup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'"$OWNER_EMAIL"'",
    "password": "'"$OWNER_PASSWORD"'",
    "firstName": "Admin",
    "lastName": "DataMarket"
  }')
case "$OWNER_RESP" in
  200) echo "Owner created" ;;
  400|409) echo "Owner already exists" ;;
  *) echo "Owner setup unexpected response: $OWNER_RESP" ;;
esac

echo "=== Logging in ==="
LOGIN_RESP=$(curl -s -c /tmp/n8n_cookies.txt -X POST "$N8N_URL/rest/login" \
  -H "Content-Type: application/json" \
  -d '{
    "emailOrLdapLoginId": "'"$OWNER_EMAIL"'",
    "password": "'"$OWNER_PASSWORD"'"
  }')
USER_ID=$(echo "$LOGIN_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"]["id"])' 2>/dev/null || true)
if [ -z "$USER_ID" ]; then
  echo "Login failed. Response: $(echo "$LOGIN_RESP" | head -c 200)"
  rm -f /tmp/n8n_cookies.txt
  exit 1
fi
echo "Logged in as user: $USER_ID"

echo "=== Getting workflow versionId ==="
curl -s -b /tmp/n8n_cookies.txt "$N8N_URL/rest/workflows/$WORKFLOW_ID" > /tmp/n8n_workflow.json
VERSION_ID=$(python3 -c "import json; print(json.load(open('/tmp/n8n_workflow.json'))['data']['versionId'])")
echo "versionId: $VERSION_ID"

echo "=== Activating workflow ==="
N8N_AUTH=$(grep n8n-auth /tmp/n8n_cookies.txt | tail -1 | awk '{print $NF}')
ACTIVATE_RESP=$(curl -s -X POST "$N8N_URL/rest/workflows/$WORKFLOW_ID/activate" \
  -H "Content-Type: application/json" \
  -H "Cookie: n8n-auth=$N8N_AUTH" \
  -d '{"versionId": "'"$VERSION_ID"'"}')
echo "$ACTIVATE_RESP" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print("Active:", d["data"]["active"], "| Triggers:", d["data"].get("triggerCount", "?"))
' 2>/dev/null || echo "Activation response: $(echo "$ACTIVATE_RESP" | head -c 200)"

rm -f /tmp/n8n_cookies.txt /tmp/n8n_workflow.json
