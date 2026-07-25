# Schemage — evidências de teste

**Data:** 2026-07-25  
**Lab:** `http://localhost:18107` (Strawberry GraphQL)  
**Plugin:** `siddhis/schemage`

## Health

- `00_health.json` — ok  
- GraphQL responde em `/graphql` e `/graphql/` (200)

## Audit automatizado

```bash
vimana run schemage --target-url http://localhost:18107 \
  --gql-path /graphql \
  --gql-auth-a 'Bearer user-a-token' --gql-auth-b 'Bearer user-b-token' \
  --gql-audit --json --ci-mode --no-channels
```

Arquivo: `03_gql_audit.json` — exit **1** (esperado)

| check | severity |
|-------|----------|
| introspection_enabled | medium |
| unbounded_query_depth | medium |
| alias_batch_overload | low |
| cross_tenant_order_idor | high |
| cross_tenant_mutation_idor | high |
| unauthenticated_sensitive_query | high |

Summary: `findings_high=3`, `findings_medium=2`, `passed=false`
