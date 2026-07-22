#!/usr/bin/env bash
# Roomgate CI example: audit open rooms, fail on high findings.
set -euo pipefail

BASE_URL="${ROOMGATE_TARGET:-http://localhost:18104}"

vimana run roomgate \
  --target-url "$BASE_URL" \
  --room-path '/ws/room/{id}' \
  --room-audit \
  --json --ci-mode --no-channels
