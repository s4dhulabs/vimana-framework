#!/usr/bin/env bash
# Pipe-friendly audit: JSON on stdout, extract actionable findings with jq.
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18101}"

vimana run streamguard \
  --scan-api "$TARGET_URL" \
  --stream-audit \
  --json \
  --no-channels \
  | tee /tmp/streamguard_last.json \
  | jq '{
      spec_id,
      base_url,
      passed: .summary.passed,
      high: .summary.findings_high,
      medium: .summary.findings_medium,
      live: .summary.live_targets,
      checks: [.findings[] | {severity, check, target, detail}]
    }'
