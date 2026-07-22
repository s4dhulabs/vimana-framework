#!/usr/bin/env bash
# CI gate for WSO aggregate report (exit 1 on high findings).
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18100}"
WS_PATH="${2:-/ws/chat}"

REPORT="$(mktemp)"

vimana run wso \
  --target-url "$TARGET_URL" \
  --ws-path "$WS_PATH" \
  --ci-mode \
  --json \
  --no-channels \
  --output "$REPORT" \
  > /dev/null

PASSED="$(jq -r '.summary.passed' "$REPORT")"
HIGH="$(jq -r '.summary.findings_high' "$REPORT")"
STEPS="$(jq -r '.summary.steps' "$REPORT")"

echo "wso CI: passed=$PASSED high=$HIGH steps=$STEPS report=$REPORT"

if [[ "$PASSED" != "true" ]]; then
  echo "High severity findings:"
  jq -c '.findings[] | select(.severity=="high")' "$REPORT"
  exit 1
fi
