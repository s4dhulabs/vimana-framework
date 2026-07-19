#!/usr/bin/env bash
# Scan API only — emit spec_id for downstream jobs.
set -euo pipefail

TARGET_URL="${1:?Usage: $0 <api-base-url>}"

vimana run boundr \
  --scan-api "$TARGET_URL" \
  --ci-mode \
  --json \
  | jq -r '.spec_id'
