#!/usr/bin/env bash
# CI gate: fail when framewire reports high-severity findings.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18103}"
FRAME_PATH="${2:-/ws/chat}"

REPORT="$(mktemp)"

vimana run framewire \
  --target-url "$TARGET_URL" \
  --frame-path "$FRAME_PATH" \
  --frame-audit \
  --ci-mode \
  --json \
  --no-channels \
  --output "$REPORT" \
  > /dev/null

PASSED="$(jq -r '.summary.passed' "$REPORT")"
HIGH="$(jq -r '.summary.findings_high' "$REPORT")"

echo "framewire CI: passed=$PASSED high=$HIGH report=$REPORT"

if [[ "$PASSED" != "true" ]]; then
  echo "High severity frame findings:"
  jq -c '.findings[] | select(.severity=="high")' "$REPORT"
  exit 1
fi
