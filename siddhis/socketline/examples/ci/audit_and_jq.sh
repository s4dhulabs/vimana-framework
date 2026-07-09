#!/usr/bin/env bash
# Pipe-friendly audit: JSON on stdout, extract actionable findings with jq.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18100}"

vimana run socketline \
  --scan-api "$TARGET_URL" \
  --ws-audit \
  --json \
  --no-channels \
  | tee /tmp/socketline_last.json \
  | jq '{
      spec_id,
      base_url,
      passed: .summary.passed,
      high: .summary.findings_high,
      medium: .summary.findings_medium,
      live: .summary.live_targets,
      checks: [.findings[] | {severity, check, target, detail}]
    }'
