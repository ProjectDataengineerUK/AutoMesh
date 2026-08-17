# DESIGN: Fase 6 — Platform Engineering, Observabilidade e Validação Integrada

> Motor determinístico de evidências, CI por domínio, telemetria portável e campanha progressiva de validação das capabilities CAP-01–CAP-10.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE6_PLATFORM_OBSERVABILITY_VALIDATION |
| **Date** | 2026-08-17 |
| **Status** | ✅ Complete (Built) |
| **Source** | `DEFINE_FASE6_PLATFORM_OBSERVABILITY_VALIDATION.md` |
| **Runtime** | Python 3.11 CI; Airflow 3.0 validation image |

---

## Architecture Overview

```text
                         repository / pull request
                                  |
                 +----------------+----------------+
                 |                                 |
           domain quality jobs                security jobs
       ruff + pytest + contracts        secret scan + dependency review
                 |                                 |
                 +---------------+-----------------+
                                 |
                     isolated Airflow DagBag
                                 |
                                 v
                   platform.validation orchestrator
                    /          |           \
             local probes  external probes  recovery probes
                    \          |           /
                     evidence records (JSON)
                                 |
                       maturity evaluator
                                 |
                  validation-report.json + .md
                                 |
                  CI artifact / local report / SDD

Runtime events ──> structured envelope ──> metrics facade ──> OTLP
 Airflow native metrics ─────────────────────────────────────> OTel Collector
                                                             /            \
                                                 local Prometheus      external backend
                                                       |
                                                    Grafana
```

The validation plane observes and classifies the platform but does not perform business actions. Probes return data; a deterministic evaluator assigns status and maturity. External probes are opt-in and cannot execute when required configuration is missing.

---

## Components

| Component | Responsibility |
|---|---|
| Capability Registry | Declares CAP-01–CAP-10, required gates and maturity rules |
| Environment Inventory | Records configured/unconfigured capabilities without reading secret values |
| Probe Interface | Standard contract for unit, DagBag, local, recovery and external validation |
| Evidence Model | Immutable validation result with reason code, SHA, timestamps and expiry |
| Validation Runner | Selects probes, enforces preconditions and writes evidence |
| Maturity Evaluator | Computes highest defensible level from current evidence |
| Report Generator | Produces machine JSON and human Markdown summaries |
| Correlation Context | Propagates event/correlation metadata without domain coupling |
| Structured Logging | Redacted JSON log records with common fields |
| Metrics Facade | Small domain API; no direct Prometheus/Sentinel imports in jobs |
| Airflow Metrics Config | Enables native OTLP export through standard environment variables |
| OTel Collector Profile | Optional local receiver and fan-out point |
| CI Workflows | Quality matrix, DagBag, security and report artifact publication |
| Recovery Harness | Deterministic fault scenarios and assertions |
| Runbooks | Versioned operational procedures linked to alerts/reason codes |

---

## Key Decisions

### Decision 1: Evidence engine is deterministic and provider-neutral

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Probe results use a fixed schema and reason-code vocabulary. The maturity evaluator contains no network calls and never infers success from missing evidence.

Rejected: generating maturity summaries with an LLM. Classification must be reproducible and auditable.

### Decision 2: JSON evidence artifacts, not an operational database

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Each validation run writes a timestamped JSON file plus a consolidated JSON/Markdown report. CI uploads artifacts; local generated evidence is ignored by Git. Only schemas, registry and selected manually reviewed evidence metadata are versioned.

Rationale: the Fase 6 control plane needs provenance, not another always-on state service.

### Decision 3: Domain CI matrix instead of one dependency monolith

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Each pipeline domain installs its own requirements and runs its tests. A separate DagBag job uses the fixed Airflow image and mounts selected DAG folders. This reduces dependency conflicts and stays within the 20-minute target.

### Decision 4: Isolated DagBag is the required Airflow gate

| Attribute | Value |
|---|---|
| **Status** | Accepted |

The successful Fase 5 pattern becomes reusable: disposable `apache/airflow:3.0.0` containers validate changed DAG domains. The full compose remains a local integration tool, not a mandatory PR gate.

### Decision 5: OpenTelemetry boundary with native Airflow export

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Application jobs call an internal metrics/logging facade. Airflow uses its native OTLP configuration and standard `OTEL_*` environment variables. An optional collector profile exports locally to Prometheus/Grafana and can later fan out to an external backend.

This follows current Airflow guidance, which supports OpenTelemetry and recommends standard environment-variable SDK configuration rather than deprecated host/port-specific keys.

### Decision 6: Metrics labels are bounded

| Attribute | Value |
|---|---|
| **Status** | Accepted |

`correlation_id`, `event_id`, raw exception text, filenames and recipient IDs are log/trace fields, not metric labels. Metric labels use bounded enums such as domain, result, reason code and source class.

### Decision 7: GitHub security gates degrade explicitly by repository capability

| Attribute | Value |
|---|---|
| **Status** | Accepted |

Local secret scanning is always available. Native dependency review, secret scanning/push protection and artifact attestations are enabled only when the repository/plan supports them. Unsupported features produce visible `SKIP_WITH_REASON:UNSUPPORTED_REPOSITORY_CAPABILITY` in platform validation.

### Decision 8: External probes are safe, scoped and opt-in

| Attribute | Value |
|---|---|
| **Status** | Accepted |

External probes require both an explicit CLI flag and capability-specific configuration. Defaults are read-only where possible; mutation probes target named test resources only. No probe provisions infrastructure or expands permissions.

### Decision 9: Maturity is computed per capability

| Attribute | Value |
|---|---|
| **Status** | Accepted |

```text
Implemented:
  unit + contract + lint current
Locally Validated:
  Implemented + local_integration current
Infrastructure Validated:
  Locally Validated + external_smoke current
Operationally Complete:
  Infrastructure Validated + recovery + alert + runbook exercise current
```

A gate marked optional for one capability does not weaken another capability's contract.

### Decision 10: Baseline commit is a manual release boundary

| Attribute | Value |
|---|---|
| **Status** | Accepted |

BUILD prepares and scans the baseline but does not create a commit, remote repository, branch protection rule or cloud resource without explicit user authorization. Evidence generated before the first commit records `commit_sha: UNVERSIONED` and cannot promote beyond local validation.

---

## File Manifest

### Validation platform

| # | File | Purpose |
|---|---|---|
| 1 | `platform/validation/__init__.py` | Package boundary |
| 2 | `platform/validation/models.py` | Evidence, status, gate and maturity models |
| 3 | `platform/validation/registry.py` | Capability registry loader/validation |
| 4 | `platform/validation/inventory.py` | Safe environment inventory |
| 5 | `platform/validation/probes.py` | Probe protocol and execution result |
| 6 | `platform/validation/runner.py` | Selection, preconditions and execution |
| 7 | `platform/validation/evaluator.py` | Deterministic maturity calculation |
| 8 | `platform/validation/report.py` | JSON/Markdown output |
| 9 | `platform/validation/cli.py` | `validate`, `report`, `inventory` commands |
| 10 | `platform/validation/capabilities.yaml` | CAP-01–CAP-10 and required gates |
| 11 | `platform/validation/evidence.schema.json` | Machine contract |
| 12 | `platform/validation/reason_codes.yaml` | Allowed skip/fail reasons |

### Observability

| # | File | Purpose |
|---|---|---|
| 13 | `pipelines/observability/__init__.py` | Package boundary |
| 14 | `pipelines/observability/context.py` | Correlation context via `contextvars` |
| 15 | `pipelines/observability/events.py` | Common event envelope |
| 16 | `pipelines/observability/logging.py` | JSON formatter and redaction filter |
| 17 | `pipelines/observability/metrics.py` | Bounded metrics facade |
| 18 | `pipelines/observability/config.py` | Env validation/fail-fast |
| 19 | `pipelines/observability/tests/test_context.py` | Context propagation |
| 20 | `pipelines/observability/tests/test_events.py` | Envelope schema |
| 21 | `pipelines/observability/tests/test_logging.py` | Secret/PII redaction |
| 22 | `pipelines/observability/tests/test_metrics.py` | Labels and metric emission |

### Probes and recovery

| # | File | Purpose |
|---|---|---|
| 23 | `scripts/validation/run_validation.py` | CLI entrypoint |
| 24 | `scripts/validation/probe_dagbag.py` | Container DagBag wrapper |
| 25 | `scripts/validation/probe_tests.py` | Test/lint result adapter |
| 26 | `scripts/validation/probe_external.py` | Safe external-probe dispatcher |
| 27 | `scripts/validation/generate_report.py` | Report entrypoint |
| 28 | `tests/platform/test_registry.py` | Registry validation |
| 29 | `tests/platform/test_evaluator.py` | Maturity and expiry cases |
| 30 | `tests/platform/test_inventory.py` | No secret values exposed |
| 31 | `tests/platform/test_report.py` | Complete CAP-01–CAP-10 report |
| 32 | `tests/recovery/test_retry_timeout.py` | Timeout/retry scenario |
| 33 | `tests/recovery/test_rate_limit.py` | 429/Retry-After scenario |
| 34 | `tests/recovery/test_poison_message.py` | DLQ continuation scenario |
| 35 | `tests/recovery/test_replay.py` | Duplicate effect scenario |
| 36 | `tests/recovery/test_checkpoint_cursor.py` | No-loss scenario |
| 37 | `tests/recovery/test_stale_precondition.py` | HITL stale-state scenario |

### CI, local stack and operations

| # | File | Purpose |
|---|---|---|
| 38 | `.github/workflows/quality.yml` | Refactor into domain test matrix |
| 39 | `.github/workflows/dagbag.yml` | Isolated Airflow validation |
| 40 | `.github/workflows/security.yml` | Local scanner + conditional native gates |
| 41 | `.github/workflows/validation-report.yml` | Consolidated artifact generation |
| 42 | `platform/observability/otel-collector.yaml` | OTLP receiver/exporters |
| 43 | `platform/observability/prometheus.yml` | Local scrape configuration |
| 44 | `platform/observability/grafana/provisioning/` | Local dashboard/data-source provisioning |
| 45 | `platform/observability/dashboards/automesh-sentinel.json` | Operational dashboard |
| 46 | `docker-compose.observability.yml` | Optional local profile/stack |
| 47 | `docs/runbooks/dlq.md` | Poison/contract failure |
| 48 | `docs/runbooks/airflow-degraded.md` | Scheduler/dag-processor resource issue |
| 49 | `docs/runbooks/external-api.md` | Timeout/429/dependency outage |
| 50 | `docs/runbooks/checkpoint-recovery.md` | Cursor/checkpoint recovery |
| 51 | `docs/runbooks/hitl-stale.md` | Stale precondition/decision recovery |
| 52 | `docs/validation/ENVIRONMENTS.md` | Safe environment inventory process |
| 53 | `docs/validation/MATURITY.md` | Status semantics and evidence expiry |

### Existing files modified

| File | Change |
|---|---|
| `pyproject.toml` | Test markers and platform lint/test config |
| `requirements-dev.txt` | Platform/observability dependencies where shared |
| `docker-compose.local.yml` | OTLP env configuration only; no heavy services inline |
| `.gitignore` | Generated evidence/telemetry data |
| `CLAUDE.md` | Validation commands and maturity status after build |
| Selected pipeline jobs | Incremental context/metric instrumentation, preserving public behavior |

---

## Code Patterns

### Pattern 1: Evidence is a closed model

```python
class EvidenceStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP_WITH_REASON = "SKIP_WITH_REASON"

@dataclass(frozen=True)
class Evidence:
    capability_id: str
    gate: Gate
    status: EvidenceStatus
    reason_code: str | None
    environment: str
    commit_sha: str
    started_at: datetime
    finished_at: datetime
    expires_at: datetime | None = None
    artifact_refs: tuple[str, ...] = ()
```

Validation rejects skip/fail without a known reason code and rejects external pass without expiry.

### Pattern 2: Probe never decides maturity

```python
class Probe(Protocol):
    capability_id: str
    gate: Gate

    def precondition(self, inventory: Inventory) -> Precondition: ...
    def run(self, context: ValidationContext) -> Evidence: ...
```

Runner behavior:

```text
precondition ready     -> run probe
precondition missing   -> SKIP_WITH_REASON
probe assertion fails  -> FAIL
probe infrastructure error -> FAIL with typed reason
```

### Pattern 3: Maturity requires current evidence

```python
def current(evidence: Evidence, now: datetime) -> bool:
    return evidence.expires_at is None or evidence.expires_at >= now
```

The evaluator considers only evidence matching the current commit for code gates. External smoke can be reused across commits only when the capability contract explicitly marks it code-independent; default is no reuse.

### Pattern 4: Safe inventory checks names, not values

```python
configured = all(name in os.environ and bool(os.environ[name]) for name in required_names)
return InventoryItem(capability="m365", configured=configured, required_names=required_names)
```

No environment value is copied, hashed or logged.

### Pattern 5: Correlation context

```python
with bind_context(correlation_id=cid, event_id=eid, source="rag"):
    logger.info("retrieval.completed", extra={"result": "success"})
```

Context is restored after the scope. Airflow task/run IDs are added by adapter code when available.

### Pattern 6: Bounded metric attributes

```python
metrics.counter("automesh.records", amount=len(records), attributes={
    "domain": "ingestion",
    "result": "accepted",
    "source_class": "market",
})
```

Dynamic IDs and raw paths are prohibited as metric attributes.

### Pattern 7: External execution requires two gates

```text
CLI --external flag present
AND inventory capability configured
AND target resource matches allowlisted test resource
```

Failure of any condition produces a skip or configuration failure before network mutation.

### Pattern 8: Generated evidence layout

```text
artifacts/validation/<run-id>/
├── evidence/*.json
├── validation-report.json
├── validation-report.md
├── junit/*.xml
└── dagbag/*.json
```

`artifacts/validation/` is ignored locally and uploaded by CI with bounded retention.

---

## Data Flow

1. CLI loads and validates capability registry/reason codes.
2. Inventory records configuration presence and runtime versions without values.
3. Runner selects probes by capability/gate/environment.
4. Preconditions yield ready or explicit skip evidence.
5. Probe executes with bounded timeout and captures safe artifact references.
6. Evidence schema is validated before writing.
7. Evaluator groups current evidence by capability and calculates maturity.
8. Reporter verifies CAP-01–CAP-10 completeness and writes JSON/Markdown.
9. CI uploads the artifact even when one or more probes fail.
10. Job exit is non-zero when required gates fail; skip policy is evaluated per gate.

Runtime observability:

1. Source creates or receives correlation context.
2. Jobs emit structured events/logs and bounded metrics.
3. Airflow emits native platform metrics to OTLP.
4. Collector exports to configured backends.
5. Dashboard/alerts link metric symptoms to runbooks and validation reason codes.

---

## Integration Points

| Integration | Mechanism | Default behavior |
|---|---|---|
| Git | `git rev-parse HEAD`; dirty-state metadata | `UNVERSIONED` before baseline |
| GitHub Actions | Matrix workflows and uploaded artifacts | No external mutation |
| Airflow | Fixed 3.0 image + `scripts/validate_dagbag.py` | Isolated by DAG domain |
| OpenTelemetry | OTLP environment variables/collector | Disabled unless endpoint configured |
| Prometheus/Grafana | Optional compose file | Local-only, manually started |
| External platforms | Capability probe adapters | Disabled unless explicit flag/config |
| Sentinel | Future OTel/log exporter | `SKIP_WITH_REASON` until configured |

Official references verified on 2026-08-17:

- Airflow metrics and OpenTelemetry: `https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/metrics.html`
- Airflow health endpoints: `https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/check-health.html`
- GitHub dependency review: `https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configure-dependency-review-action`
- GitHub push protection: `https://docs.github.com/en/code-security/concepts/secret-security/push-protection`
- GitHub artifact attestations: `https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations`

---

## Testing Strategy

| Level | Scope | Gate |
|---|---|---|
| Unit | Models, inventory, evaluator, reporter, context, redaction, metrics | Required on every change |
| Schema/contract | YAML registry, evidence JSON, event envelope | Required on every change |
| Domain | Existing pipeline suites in isolated matrix | Required for affected domain |
| DagBag | Every discovered DAG under Airflow 3.0 | Required on every DAG change/main |
| Recovery | Six deterministic scenarios | Required on main; selected tests on PR |
| Local integration | Redpanda/Postgres/Delta/SQLite components | Scheduled/manual or affected change |
| External smoke | One capability/service at a time | Explicit dispatch with protected secrets |
| E2E | Full eligible chain | Manual after current smokes |

Required evaluator tests:

- Missing gate cannot promote maturity.
- Skip never promotes maturity.
- Expired external evidence is ignored.
- Wrong commit code evidence is ignored.
- Unknown capability/reason code fails schema validation.
- Report always contains exactly CAP-01–CAP-10.
- Mixed pass/fail/skip remains visible.

---

## CI Architecture

### `quality.yml`

- Detect affected domain paths.
- Matrix across domain requirement files using Python 3.11.
- Run Ruff globally once and pytest per domain.
- Produce JUnit and timing artifacts.
- Cancel superseded PR runs.

### `dagbag.yml`

- Discover DAG domains.
- Run fixed Airflow 3.0 container per domain.
- Install only parse-time dependencies declared for that domain.
- Upload structured DagBag result on success/failure.

### `security.yml`

- Run a repository-local secret scanner independent of GitHub plan.
- Run dependency review only for pull requests when supported.
- Generate dependency inventory/SBOM where tooling permits.
- Native GitHub secret protection remains repository-admin configuration, documented but not assumed.

### `validation-report.yml`

- `workflow_run`/manual entry after prerequisite jobs.
- Download or generate evidence artifacts.
- Consolidate CAP-01–CAP-10 report.
- Upload report even on failed gates.
- No artifact attestation unless repository visibility/plan supports it.

---

## Error Handling

| Failure | Evidence status/reason | Exit behavior |
|---|---|---|
| Required assertion fails | `FAIL:ASSERTION_FAILED` | Non-zero |
| Invalid config/schema | `FAIL:CONFIGURATION_ERROR` | Non-zero |
| Required dependency unavailable unexpectedly | `FAIL:DEPENDENCY_UNAVAILABLE` | Non-zero |
| Credential intentionally absent for optional smoke | `SKIP_WITH_REASON:MISSING_CREDENTIAL` | Zero for optional gate |
| Infra not provisioned | `SKIP_WITH_REASON:INFRA_NOT_PROVISIONED` | Zero for optional gate |
| Evidence expired | `SKIP_WITH_REASON:STALE_EVIDENCE` | Maturity not promoted |
| Docker resource exhaustion | `SKIP_WITH_REASON:RESOURCE_LIMIT` only for optional integration; required DagBag uses isolated fallback | Depends on gate |
| Reporter cannot account for all capabilities | `FAIL:REPORT_INCOMPLETE` | Non-zero |

Exceptions are summarized with redaction. Raw tracebacks may be artifacts only after secret filtering.

---

## Configuration

```yaml
validation:
  evidence_ttl_days: 30
  output_dir: artifacts/validation
  external_enabled: false
  default_timeout_seconds: 300
ci:
  target_python: "3.11"
  target_airflow: "3.0.0"
  domain_timeout_minutes: 20
observability:
  enabled: false
  service_name: automesh
  metric_prefix: automesh
  exporter: none
```

Environment names are declared per probe. Configuration validation reports only missing names, never values.

---

## Security Considerations

- Baseline preflight checks ignored/local artifacts and scans candidate files before any commit.
- CI permissions default to `contents: read`; write permissions exist only in narrowly scoped future jobs.
- Third-party actions are pinned to immutable commit SHAs in final workflows where practical.
- Fork PRs never receive protected external credentials.
- External jobs use protected environments/manual approval.
- Probe target allowlists prevent production resource mutation.
- Evidence artifact names and content undergo path and secret redaction.
- Free-form logs/reasons are not metric labels.
- GitHub plan-dependent security controls are additive; local scanner remains mandatory.
- Artifact attestations are conditional because private repository support depends on plan.

---

## Observability

The platform observes itself through the same evidence model:

| Signal | Measurement |
|---|---|
| CI reliability | Result and duration per workflow/domain |
| Validation coverage | Evidence count per capability/gate/status |
| Evidence freshness | Days until expiry/stale count |
| DAG health | Import errors and discovered DAG count |
| Recovery confidence | Scenario result and last successful exercise |
| Telemetry health | Export failures and collector health |

Alert-to-runbook mapping is versioned in capability configuration. An alert without a runbook reference fails the operational-completeness gate.

---

## Build Order

1. Evidence models, schemas, reason codes and registry.
2. Evaluator/report with complete unit tests.
3. Safe inventory and CLI.
4. CI domain matrix and isolated DagBag.
5. Correlation, structured logging and metrics facade.
6. Incremental instrumentation of critical paths.
7. Recovery harness and runbooks.
8. Optional local OTel/Prometheus/Grafana stack.
9. Baseline preflight report.
10. External inventory and smoke campaign only after explicit authorization/configuration.

Steps 1–9 require no cloud writes. Step 10 is a separate controlled iteration.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-17 | Codex + usuário | Initial platform, evidence, CI and observability design |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_FASE6_PLATFORM_OBSERVABILITY_VALIDATION.md`

The first BUILD iteration covers steps 1–4 and baseline preflight. Observability runtime instrumentation and recovery harness follow incrementally so existing behavior remains stable.
