#!/usr/bin/env bash
# CI gate: fail pipeline when streamguard reports high-severity streaming findings.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18101}"
STREAM_PATH="${2:-/events}"

REPORT="$(mktemp)"

vimana run streamguard \
  --target-url "$TARGET_URL" \
  --stream-path "$STREAM_PATH" \
  --stream-audit \
  --ci-mode \
  --json \
  --no-channels \
  --output "$REPORT" \
  > /dev/null

PASSED="$(jq -r '.summary.passed' "$REPORT")"
HIGH="$(jq -r '.summary.findings_high' "$REPORT")"

echo "streamguard CI: passed=$PASSED high=$HIGH report=$REPORT"

if [[ "$PASSED" != "true" ]]; then
  echo "High severity streaming findings:"
  jq -c '.findings[] | select(.severity=="high")' "$REPORT"
  exit 1
fi
