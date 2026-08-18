# DESIGN: Fase 8 — Validação Externa e Readiness Databricks

> Technical design for safe, opt-in validation and publication of existing AutoMesh artifacts.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE8_EXTERNAL_VALIDATION |
| **Date** | 2026-08-18 |
| **Author** | design-agent |
| **DEFINE** | `DEFINE_FASE8_EXTERNAL_VALIDATION.md` |
| **Status** | ✅ Shipped |

## Architecture Overview

```text
CLI / Airflow task
        |
  mode + config loader  -----> redaction / secret guard
        |
  preflight gates (auth, host, UC, permissions, contracts)
        |                         |
        | fail/skip               | pass
        v                         v
  evidence report <----- dry-run planner -----> publish adapter
                                      |              |
                              SQL/Lakeview/Jobs API  |
                                      v              v
                              reconcile + freshness + evidence
```

The local path never imports or calls cloud clients unless `publish` is explicitly selected. External state changes are preceded by preflight and dry-run, and every result is represented as `PASS`, `FAIL`, or `SKIP_EXTERNAL`.

## Components and Manifest

| Component | Proposed path | Responsibility |
|---|---|---|
| CLI | `pipelines/external_validation/cli.py` | Parse mode, config and exit behavior |
| Config | `pipelines/external_validation/config.py` | Env allowlist, validation and redaction |
| Gates | `pipelines/external_validation/gates.py` | Connectivity, UC, permissions and contract checks |
| Planner | `pipelines/external_validation/planner.py` | Deterministic desired-state plan |
| Adapter | `pipelines/external_validation/databricks_adapter.py` | Narrow SDK/REST boundary, lazy import |
| Reconciliation | `pipelines/external_validation/reconcile.py` | Gold metric and freshness comparison |
| Evidence | `pipelines/external_validation/evidence.py` | JSON/Markdown report with redaction |
| DAG | `pipelines/external_validation/dags/dag_external_validation.py` | Optional scheduled/manual orchestration |
| Contracts | `pipelines/external_validation/contracts/*.yaml` | Gate and object expectations |
| Tests | `pipelines/external_validation/tests/` | Unit, security and integration-contract tests |
| Docs | `docs/external-validation/README.md` | Operator runbook and authorization boundary |
| CI | `.github/workflows/external-validation.yml` | Local gates; external job manual-dispatch only |

## Execution Contract

```text
mode = preflight | dry-run | publish
result = PASS | FAIL | SKIP_EXTERNAL
```

- `preflight`: no external mutation; validates configuration and access.
- `dry-run`: builds desired-state object plan; no external mutation.
- `publish`: requires explicit confirmation flag, successful preflight and dry-run evidence.
- Missing required cloud context produces `SKIP_EXTERNAL`; malformed or unsafe context produces `FAIL`.

## Key Decisions (ADRs)

### ADR-001: External calls behind a lazy adapter

**Accepted.** Keep cloud SDK imports and network calls isolated so local tests remain deterministic and dependency-light.

### ADR-002: Publish requires two-phase confirmation

**Accepted.** A successful preflight plus dry-run artifact and explicit `--confirm-publish` are required before mutation.

### ADR-003: No provisioning in this phase

**Accepted.** The harness validates a supplied workspace but does not create accounts, clusters, catalogs, schemas or paid resources.

### ADR-004: Evidence is append-only and redacted

**Accepted.** Reports include commit, timestamp, gate results, object identifiers and reconciliation values, while secrets and tokens are removed by allowlist/redaction.

## Gate Order

1. Configuration/schema validation.
2. Secret and log-safety scan.
3. Connectivity and workspace identity.
4. Unity Catalog catalog/schema existence.
5. Permission checks (read, create/update, SQL execution).
6. Gold/dashboard contract validation.
7. Dry-run desired-state plan.
8. Optional publish.
9. Reconciliation, freshness and evidence finalization.

## Testing Strategy

| Layer | Coverage |
|---|---|
| Unit | Config, redaction, gate classification, planner idempotency, reconciliation |
| Contract | Existing Gold YAML/SQL/Lakeview manifests and expected object names |
| Security | Secret fixtures, unsafe URLs, log capture and report redaction |
| Integration contract | Fake Databricks adapter verifies call order and no mutation on failed gates |
| External smoke | Manual/approved job against test workspace only; never required for local CI |

## Failure Handling and Observability

- Each gate emits stable code, severity, message and remediation hint.
- Publish stops at the first unsafe gate; reconciliation failures never get downgraded to success.
- Reports are written outside tracked data paths by default and can be uploaded as CI artifacts.
- Metrics: duration per gate, pass/fail/skip count, object mutation count, reconciliation delta and freshness lag.

## Security and Cost Controls

- Environment variable allowlist; reject credentials in YAML/CLI arguments where feasible.
- Redact values matching token/password/secret patterns before console or report output.
- Manual dispatch and environment approval for external publish.
- Read-only preflight default; no cluster creation or destructive SQL.

## Acceptance Mapping

All AT-001–AT-012 from DEFINE map to tests in `pipelines/external_validation/tests/`; AT-005/AT-006/AT-011 additionally map to the manual external smoke checklist.

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-18 | design-agent | Harness architecture, gate order, adapter and validation strategy |
| 1.1 | 2026-08-18 | ship-agent | Shipped and archived after local validation and CI workflow publication |

## Next Step

**Completed:** Shipped and archived on 2026-08-18.
