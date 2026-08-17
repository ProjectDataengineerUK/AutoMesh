# BUILD REPORT: Fase 5 — Entrega Segura e Human-in-the-Loop

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE5_ENTREGA_HITL |
| **Date** | 2026-08-14 |
| **Status** | Implemented — infrastructure validation pending |
| **Design** | `../features/DESIGN_FASE5_ENTREGA_HITL.md` |

## Summary

| Metric | Result |
|---|---|
| Production/config/test files | 42 versionáveis em `pipelines/delivery/` |
| Python LOC | ~1,029 incluindo testes |
| Delivery tests | 18 passed, 1 skipped (DagBag sem Airflow no host) |
| Remediation regression selection | 23 passed |
| Ruff | All checks passed em `pipelines/` |
| External calls | Não executadas |

## Task Execution

| Area | Status | Evidence |
|---|---|---|
| Models and state machines | Complete | Enums/dataclasses + terminal transition tests |
| Idempotency | Complete | Stable keys, duplicate request reuse and exclusive claims |
| Authorization | Complete | Deny-by-default policy and unauthorized actor test |
| Adaptive Cards | Complete | `Action.Execute` carries only decision reference/schema version |
| Teams proactive adapter | Implemented | HTTP adapter with typed transient/permanent errors; real bot token pending |
| Outlook fallback | Implemented | Graph `sendMail`; external permission/mailbox pending |
| Transactional local storage | Complete | SQLite WAL + `BEGIN IMMEDIATE`; persistence smoke test passed |
| Dispatcher | Complete | Claim, retry, terminal failure and fallback tests |
| Bot domain handler | Complete | Approval, rejection, expiry and replay tests |
| MLflow application | Complete | Alias precondition and stale-state tests |
| Reconciler | Complete | Expiry test |
| Airflow DAGs | Implemented structurally | Four DAG files; DagBag test skipped on host |
| Teams-hosted bot middleware | Pending infrastructure | Adapter boundary exists; official authentication middleware must wrap it |

## Files Created

The build created the complete `pipelines/delivery/` package with:

- `common/`: models, storage, SQLite adapter, runtime, cards, auth, Teams and Graph clients.
- `jobs/`: request builder, dispatcher, applications and reconciler.
- `bot/`: framework-neutral authenticated-handler boundary.
- `dags/`: collect, dispatch, apply and reconcile.
- `contracts/`: outbox, decision and application contracts.
- `infra/`: Teams manifest template and external validation checklist.
- `tests/`: nine test modules.

It also updated `requirements-dev.txt`, `.gitignore` and `docker-compose.local.yml`.

## Verification Results

### Lint Check

```text
python -m ruff check pipelines
All checks passed!
```

### Tests

```text
python -m pytest pipelines/delivery/tests -q -p no:cacheprovider
16 passed, 1 skipped

targeted remediation regression selection
23 passed
```

The full repository suite was not rerun because this managed Windows environment denies pytest access to its temporary directory for the Delta-backed tests. The new delivery tests do not depend on that directory and passed. CI on Linux is configured to run the complete suite.

### Persistence Smoke Test

A real SQLite file was created, a decision was committed, the store was reopened and the record was read back. Temporary DB/WAL files were removed afterward.

## Deviations from Design

| Deviation | Reason | Impact |
|---|---|---|
| SQLite replaced Delta as the reference local decision store | Approval and claims require transactional compare-and-set; rewriting Delta tables would repeat the checkpoint race corrected in the remediation | Safer local semantics; a managed transactional backend is still required for HA production |
| Added `runtime.py` and `sqlite_storage.py` | Keep domain store testable while giving independent Airflow processes persistent state | Two files beyond original manifest |
| Collector accepts normalized manual events; self-healing publishes PR results automatically | Other future producers may still use the normalized collector contract | PR review integration is automatic and idempotent |
| Bot `app.py` is an adapter boundary, not a hosted web server | Deploying without official Teams authentication middleware would be insecure | Cannot be marked Infrastructure Validated until a real Teams app wraps the handler |

## Acceptance Test Verification

| IDs | Status | Evidence |
|---|---|---|
| AT-001, AT-002 | Pass locally | Dispatcher success and repeat tests |
| AT-003–AT-007 | Pass locally | Handler approval/replay/auth/rejection/expiry tests |
| AT-008 | Partial | Teams failure/fallback unit tests; no Graph call real |
| AT-009, AT-010 | Pass locally | Fake registry promotion and stale precondition tests |
| AT-011 | Pass by design | No GitHub mutation dependency exists in `pipelines/delivery` |
| AT-012 | Pass locally | Informational card rendering/dispatch path |

## Blockers

These block `Infrastructure Validated`, not the local `Implemented` status:

1. Microsoft 365 test tenant and organizational Teams app catalog.
2. Hosted bot endpoint using official Teams authentication middleware.
3. Conversation references and runtime bot token acquisition.
4. Graph `Mail.Send` restricted to a dedicated test mailbox.
5. MLflow/Unity Catalog service identity and registry smoke test.
6. Additional direct producers beyond the unified self-healing PR result, when needed.
7. Full DagBag and repository test suite in CI/Airflow container.

## Final Status

### Overall: IMPLEMENTED, NOT INFRASTRUCTURE VALIDATED

The local domain and safety properties are ready. Successful self-healing PR results now flow through a separate mapped Airflow task into the delivery outbox, so delivery retries cannot recreate a branch or PR. Do not enable external delivery or model promotion until the infrastructure checklist is executed.

## Integration Iteration — 2026-08-17

- Added `jobs/source_adapters.py` to translate successful self-healing PR results into the normalized delivery contract.
- Changed `dag_self_healing_diagnose` to return structured results and enqueue delivery in an independent mapped task.
- Missing `DELIVERY_REVIEW_RECIPIENT` skips notification explicitly without failing PR creation.
- Duplicate self-healing results reuse the same notification and decision.
- Verification: delivery `18 passed, 1 skipped`; self-healing selection `25 passed, 1 skipped`; full Ruff clean.
- Docker compose validated syntactically. The full stack reproduced the documented local resource limitation, so DagBag validation was moved to isolated disposable Airflow 3.0 containers.
- Isolated Airflow 3.0 DagBag: all four delivery DAGs loaded with `ERRORS={}`.
- Isolated Airflow 3.0 DagBag with Delta dependencies: `dag_self_healing_diagnose` loaded with `ERRORS={}` after the delivery integration.
- Added reusable `scripts/validate_dagbag.py` for CI/local container validation.

## Next Step

Run an integration iteration for the normalized source adapters and Airflow DagBag, then provision the Microsoft test resources for the external smoke tests.
