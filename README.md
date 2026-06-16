# omnibioai-api-gateway

**Zero-trust API gateway for the OmniBioAI platform.**

Single enforced entry point for all service traffic. Every request
is authenticated, authorized, quota-checked, and audited before
reaching any backend service.

---

## Architecture

```
Internet / Client / Studio

↓

api-gateway :8080        ← single entry point

↓

TraceMiddleware          ← generates X-Trace-Id UUID

↓

AuthMiddleware           ← JWT validation via IAM client + Redis cache

↓

PolicyMiddleware         ← RBAC/ABAC via policy-engine

↓

HPCMiddleware            ← GPU/CPU quota via hpc-policy-engine

↓

AuditMiddleware          ← async audit log via security-audit

↓

target service           ← workbench / tes / toolserver / rag / lims
```

**Failure policy:**

| Layer | On failure |
|-------|-----------|
| Auth | FAIL CLOSED → HTTP 401 |
| Policy | FAIL CLOSED → HTTP 403 |
| HPC quota | FAIL CLOSED → HTTP 403 |
| Audit | FAIL OPEN → ignored |

---

## Features

- JWT authentication via IAM client (Redis-cached, sub-ms validation)
- RBAC/ABAC policy enforcement on every request
- GPU/CPU quota governance for compute requests
- Async audit logging via Redis Streams (never blocks requests)
- Service-to-service (S2S) token validation
- Distributed trace ID propagation (X-Trace-Id header)
- Redis pub/sub cache invalidation on logout
- Rate limiting on auth endpoints (via nginx — 10 req/min, burst 5)

---

## Middleware Stack

Middleware is applied LIFO — last added runs first for requests:

| Order | Middleware | Responsibility |
|-------|-----------|----------------|
| 1 | TraceMiddleware | Generate X-Trace-Id, attach to request state |
| 2 | AuthMiddleware | Validate JWT via IAM client |
| 3 | PolicyMiddleware | RBAC/ABAC authorization decision |
| 4 | HPCMiddleware | GPU/CPU quota check (compute paths only) |
| 5 | AuditMiddleware | Fire async audit event to Redis Streams |

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | — | Gateway health check |
| `/auth/verify` | GET | JWT | Verify token (used by nginx auth_request) |
| `/api/*` | ALL | JWT | Proxy to target service |

### Health check
```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

### All other requests require JWT
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/tools
```

---

## Service Routing

| Path prefix | Target service |
|-------------|----------------|
| `/api/workbench/*` | workbench :8000 |
| `/api/tes/*` | tes :8081 |
| `/api/tools/*` | toolserver :9090 |
| `/api/models/*` | model-registry :8095 |
| `/api/rag/*` | rag :8096 |
| `/api/lims/*` | lims :7000 |

---

## Internal Headers Propagated

| Header | Description |
|--------|-------------|
| `X-Trace-Id` | UUID per request for distributed tracing |
| `X-User-Id` | Authenticated user ID |
| `X-Internal-Service` | Marks request as internal (gateway-verified) |

---

## Running

### Via OmniBioAI Studio (recommended)

```bash
cd ~/Desktop/machine/omnibioai-studio
docker compose up -d api-gateway
```

Access: `http://localhost:8080`

### Environment variables

Set in `omnibioai-studio/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `IAM_URL` | `http://omnibioai-auth:8000` | Auth service URL |
| `POLICY_URL` | `http://omnibioai-policy-engine:8001` | Policy engine URL |
| `HPC_URL` | `http://omnibioai-hpc-policy-engine:8002` | HPC policy URL |
| `REDIS_URL` | `redis://redis:6379` | Redis for token cache + pub/sub |
| `JWT_SECRET` | — | JWT signing secret (auto-generated) |
| `ROUTE_TIMEOUT` | `15` | Upstream request timeout (seconds) |

---

## Testing

```bash
cd ~/Desktop/machine/omnibioai-api-gateway
pytest tests/ -v --cov=app

# 33 tests passing
# 74% coverage
# Covers: auth middleware, policy middleware, HPC middleware,
#         trace middleware, config, gateway router
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Uvicorn |
| Auth | IAM client (httpx async + Redis cache) |
| Cache invalidation | Redis pub/sub |
| Tracing | UUID trace IDs via middleware |
| Proxying | httpx reverse proxy |

---

## Related Services

| Service | Role |
|---------|------|
| `omnibioai-auth` | JWT issuance and validation |
| `omnibioai-iam-client` | Async IAM client with Redis cache |
| `omnibioai-policy-engine` | RBAC/ABAC authorization decisions |
| `omnibioai-hpc-policy-engine` | GPU/CPU quota governance |
| `omnibioai-security-audit` | Async audit event consumer |
| `omnibioai-security-sdk` | SDK wrapping the full security stack |
| `omnibioai-studio` | Manages gateway container lifecycle |

---

## License

Apache 2.0

---

*Part of the [OmniBioAI](https://github.com/man4ish/omnibioai-studio) platform.*
