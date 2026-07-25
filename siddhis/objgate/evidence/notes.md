# Objgate — evidências de teste

**Data:** 2026-07-22  
**Lab:** `http://localhost:18105` (Django REST Framework, container `objgate-test-app`)  
**Plugin:** `siddhis/objgate`  
**Ambiente:** `.venv/bin/python /usr/local/bin/vimana`

## 1. Lab health

`01_health.json` — `GET /health` → `{"status":"ok","service":"objgate-lab"}`

`02_catalog.json` — seed:

| id | owner  | secret            |
|----|--------|-------------------|
| 1  | user-a | tenant-a-secret   |
| 2  | user-b | tenant-b-secret   |
| 3  | ops    | ops-secret        |

Tokens: `Bearer user-a-token` / `Bearer user-b-token`

## 2. Probes manuais (curl)

Arquivo: `03_manual_probes.txt`

| Probe | Resultado |
|-------|-----------|
| `GET /api/orders/1/` sem auth | **200** + secret (CWE-306) |
| `GET /api/secure/orders/2/` como user-a | **200** + secret de user-b (BOLA) |
| `GET /api/secure/orders/2/` sem auth | **403** (auth ok) |
| `GET /api/admin/orders/1/` como user-a | **200** (BFLA) |

## 3. Audit automatizado — open orders

Comando:

```bash
vimana run objgate --target-url http://localhost:18105 \
  --obj-path '/api/orders/{id}/' --obj-id-a 1 --obj-id-b 2 \
  --obj-audit --json --ci-mode --no-channels
```

Arquivo: `04_open_orders_audit.json`  
Exit code: **1** (`04_open_orders_exit.txt`) — esperado com `--ci-mode` quando há high findings.

| check | severity | HTTP |
|-------|----------|------|
| unauthenticated_object_access | high | 200 |
| cross_tenant_object_idor (GET) | high | 200 |
| cross_tenant_object_idor (PATCH) | high | 200 |
| membership_baseline | info | — |
| vertical_privilege_object | medium | 200 |

Summary: `findings_high=3`, `findings_medium=1`, `passed=false`

## 4. Audit automatizado — secure orders (auth + BOLA)

Comando:

```bash
vimana run objgate --target-url http://localhost:18105 \
  --obj-path '/api/secure/orders/{id}/' \
  --obj-id-a 1 --obj-id-b 2 \
  --obj-auth-a 'Bearer user-a-token' --obj-auth-b 'Bearer user-b-token' \
  --obj-methods GET,PATCH --obj-audit --json --ci-mode --no-channels
```

Arquivo: `05_secure_orders_audit.json`  
Exit code: **1** (`05_secure_orders_exit.txt`)

| check | severity | HTTP | Nota |
|-------|----------|------|------|
| cross_tenant_object_idor (GET) | high | 200 | user-a → order 2 |
| cross_tenant_object_idor (PATCH) | high | 200 | |
| membership_baseline | info | — | A→1 e B→2 OK |
| vertical_privilege_object | medium | 200 | `/api/admin/orders/1/` |

**Não** reportou `unauthenticated_object_access` no path secure (correto: 403 sem token).

Summary: `findings_high=2`, `findings_medium=1`, `passed=false`

## Veredito

Lab DRF `:18105` vulnerável como esperado; objgate detecta unauth, BOLA horizontal (GET/PATCH) e BFLA vertical. Path “secure” exige auth mas falha ownership — evidenciado nos JSONs acima.
