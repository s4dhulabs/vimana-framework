#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:18100}"

vimana run wso \
  --scan-api "$TARGET_URL" \
  --json \
  --no-channels \
  | tee /tmp/wso_last.json \
  | jq '{
      plugin,
      orchestrator,
      spec_id,
      base_url,
      passed: .summary.passed,
      high: .summary.findings_high,
      medium: .summary.findings_medium,
      steps: .steps,
      checks: [.findings[] | {plugin: (.check), severity, detail}]
    }'
