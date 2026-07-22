#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:?Usage: $0 <api-base-url>}"

vimana run framewire \
  --scan-api "$TARGET_URL" \
  --ci-mode \
  --json \
  | jq -r '.spec_id'
