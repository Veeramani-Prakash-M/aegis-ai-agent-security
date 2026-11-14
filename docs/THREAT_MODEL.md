# AEGIS Threat Model (MVP)

## Assets

- Agent profile configuration
- Synthetic evaluation prompts and results
- Report and dashboard integrity
- Local database availability

## Trust boundaries

- Browser to FastAPI API boundary
- API to persistence layer
- Future model adapter boundary (not present in this MVP)
- Future tool adapter boundary (only synthetic mock events are present)

## In-scope risks

- Malformed API input
- Script injection through displayed user-controlled profile fields
- Incorrect scoring or scenario selection
- Accidental interpretation of synthetic findings as real-world assurance
- Unintended external side effects during attack simulation

## Current mitigations

- Pydantic request validation and bounded string lengths
- SQLAlchemy parameterized persistence operations
- Frontend HTML escaping for dynamic data
- Deterministic local simulator; no live LLM calls or external tools
- Synthetic canary values only
- Container hardening in the provided Compose configuration
- Reports explicitly document simulator limitations

## Out of scope / required before production

- Authentication, authorization, tenant isolation and account recovery
- Public API rate limiting and abuse controls
- CSRF/CORS policy for a production domain
- Provider credential management and model isolation
- Safe sandboxing of arbitrary tools or code execution
- Production-grade secrets handling, monitoring, backups and database migrations
- Independent security review and formal benchmark validation

## Safety rule

Never point the initial attack runner at third-party systems. A future real-agent adapter must require an explicit test target, ownership/authorization confirmation, a sandbox boundary, and a no-side-effect tool policy.
