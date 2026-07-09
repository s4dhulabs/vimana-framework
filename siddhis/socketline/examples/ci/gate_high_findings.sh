#!/usr/bin/env bash
# CI gate: fail pipeline when socketline reports high-severity WebSocket findings.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18100}"
WS_PATH="${2:-/ws/chat}"

REPORT="$(mktemp)"

vimana run socketline \
  --target-url "$TARGET_URL" \
  --ws-path "$WS_PATH" \
  --ws-audit \
  --ci-mode \
  --json \
  --no-channels \
  --output "$REPORT" \
  > /dev/null

# summary.passed is the CI-friendly boolean gate
PASSED="$(jq -r '.summary.passed' "$REPORT")"
HIGH="$(jq -r '.summary.findings_high' "$REPORT")"

echo "socketline CI: passed=$PASSED high=$HIGH report=$REPORT"

if [[ "$PASSED" != "true" ]]; then
  echo "High severity WebSocket findings:"
  jq -c '.findings[] | select(.severity=="high")' "$REPORT"
  exit 1
fi
