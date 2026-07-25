# Fetchbane — evidências de teste

**Data:** 2026-07-25  
**Lab:** `http://localhost:18106` (Flask + canary `127.0.0.1:9999`)  
**Plugin:** `siddhis/fetchbane`

## Health / canary manual

- `00_health.json` — ok  
- `01_manual_canary.json` — `GET /preview?url=http://127.0.0.1:9999/secret` refletiu `FETCHBANE_CANARY_SECRET`

## Audit automatizado

```bash
vimana run fetchbane --target-url http://localhost:18106 \
  --ssrf-endpoint /preview --ssrf-audit --json --ci-mode --no-channels
```

Arquivo: `03_preview_audit.json` — exit **1** (esperado)

| Achados | |
|---------|---|
| findings_high | 7 |
| findings_medium | 1 |
| passed | false |

Checks observados: `ssrf_canary_reflection` (loopback/bypass), `ssrf_cloud_metadata`, `ssrf_file_scheme`.
