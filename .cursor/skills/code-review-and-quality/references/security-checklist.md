# Security Review Checklist

Use at system boundaries and anywhere untrusted data enters the stack. Expand with project-specific threat models as needed.

## Secrets and configuration

- [ ] No secrets, tokens, or private keys in code, tests, logs, or committed config
- [ ] Secrets loaded from env/secret manager; rotation path understood if applicable

## Authentication and authorization

- [ ] Protected routes/actions require auth; default-deny where appropriate
- [ ] Authorization checks resource ownership/role, not only authentication
- [ ] Session/token handling follows project standards (expiry, rotation, CSRF if web)

## Input and output

- [ ] User and external input validated (type, length, format) at boundaries
- [ ] SQL/parameters use bound queries or ORM; no string-concatenated SQL
- [ ] Shell commands avoid untrusted interpolation; prefer safe APIs
- [ ] HTML/JSON/XML outputs encoded or escaped appropriately (XSS)
- [ ] File uploads restricted by type/size; stored outside web root if served indirectly

## Dependencies and supply chain

- [ ] New dependencies justified; license compatible; maintained
- [ ] Known CVEs checked (`npm audit`, `pip-audit`, GitHub advisories, etc.)

## Data and trust

- [ ] Data from APIs, files, queues, and logs treated as untrusted until validated
- [ ] Sensitive data not logged; PII handling matches policy
- [ ] Crypto uses vetted libraries and correct primitives (no custom crypto)

## Related

Main workflow: [../SKILL.md](../SKILL.md) (Security axis).
