#!/usr/bin/env bash
# CI gate: fail pipeline when boundr reports high-severity upload findings.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18102}"
UPLOAD_PATH="${2:-/upload}"

REPORT="$(mktemp)"

vimana run boundr \
  --target-url "$TARGET_URL" \
  --upload-endpoint "$UPLOAD_PATH" \
  --upload-audit \
  --ci-mode \
  --json \
  --no-channels \
  --output "$REPORT" \
  > /dev/null

PASSED="$(jq -r '.summary.passed' "$REPORT")"
HIGH="$(jq -r '.summary.findings_high' "$REPORT")"

echo "boundr CI: passed=$PASSED high=$HIGH report=$REPORT"

if [[ "$PASSED" != "true" ]]; then
  echo "High severity upload findings:"
  jq -c '.findings[] | select(.severity=="high")' "$REPORT"
  exit 1
fi
