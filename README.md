# OmniBioAI API Gateway

Central zero-trust entry point for the OmniBioAI ecosystem.

## Responsibilities

- Authentication (IAM validation)
- Policy enforcement (RBAC / ABAC)
- Service-to-service security (S2S)
- Request routing
- Audit-ready traffic control

---

## Architecture

Client → Gateway → Services

Gateway enforces:
- Identity
- Policy
- Security
- Routing

---

## Features

- JWT authentication
- S2S token validation
- Policy engine integration
- Reverse proxy routing
- Microservice isolation

---

## Services Routed

- Workbench
- TES
- Toolserver
- Model Registry
- RAG system

---

## Deployment

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
````

---

## Security Model

Zero Trust:

* no direct service exposure
* all traffic must pass gateway
* every request is validated + audited

```

---

# 🧬 What you achieved now

You now have:

✔ IAM system  
✔ Policy engine  
✔ Audit system  
✔ Security SDK  
✔ API Gateway (NEW)

---

# 🚨 Result: You now have AWS-like architecture

This is now equivalent to:

- AWS API Gateway
- IAM
- CloudTrail
- OPA policy layer

…but specialized for:
> HPC + bioinformatics + AI workflows




