# DESIGN: Fase 7 — Produtos Gold e BI no Databricks

> Technical design for implementing governed Gold products and executive/operational Lakeview consumption.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | FASE7_GOLD_BI_DATABRICKS |
| **Date** | 2026-08-17 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_FASE7_GOLD_BI_DATABRICKS.md](./DEFINE_FASE7_GOLD_BI_DATABRICKS.md) |
| **Status** | ✅ Complete (Built) |

---

## Architecture Overview

```text
 Silver Delta       Insights/MLflow       FinOps       Fase 6 Evidence
      |                    |                 |                |
      +--------------------+-----------------+----------------+
                           |
                 Gold contract + quality gate
                           |
             +-------------+--------------+
             |                            |
       Local fixture runner          Databricks SQL/Lakeflow
       (DuckDB/SQL-compatible)       Delta Gold / Unity Catalog
             |                            |
             +-------------+--------------+
                           |
                    Semantic SQL views
                    /                 \
          Executive Lakeview      Operational Lakeview
```

The MVP has one transformation boundary and two consumer contracts. Local execution validates schemas, formulas, keys and report completeness without pretending to validate a Databricks workspace. External publication is a separate opt-in adapter.

---

## Components

| Component | Purpose | Technology |
|---|---|---|
| Gold contracts | Define grain, keys, owners, metrics, sensitivity and freshness | YAML + JSON Schema |
| Gold build library | Deterministic incremental aggregation and deduplication | Python, pandas/SQL fixtures; Databricks SQL adapter |
| Gold SQL models | Four products for market/insights, lost sales, FinOps and platform health | Databricks SQL / Delta |
| Metric registry | Versioned formulas and dashboard metadata | YAML |
| Quality gates | PK, uniqueness, completeness, freshness, volume and contract checks | Python + SQL assertions |
| Semantic views | Stable names and dimensions for two dashboards | Databricks SQL views |
| Dashboard manifests | Executive and operational Lakeview definitions | JSON |
| Publication adapter | External create/update with preconditions and evidence | Databricks SDK/REST, opt-in |
| Gold DAG | Orchestrates local/external build and evidence | Airflow 3 TaskFlow |
| Test fixtures | Reproducible source, edge and failure data | JSON/CSV/Python fixtures |

---

## Key Decisions

### Decision 1: Delta Gold is the single MVP product boundary

| Attribute | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |

**Context:** Existing domains already produce Delta-compatible Silver, insights, FinOps and validation artifacts. A second warehouse would duplicate formulas before the first consumer is proven.

**Choice:** Build Gold products in Delta and expose Databricks SQL views over those products.

**Rationale:** This follows the medallion and Lakeflow Gold aggregation patterns with confidence 0.95, preserves lineage and minimizes new dependencies.

**Alternatives Rejected:**

1. Snowflake/dbt — rejected for MVP because it duplicates transformation and requires external account setup.
2. Fabric/Power BI — rejected for MVP because the selected user direction is Databricks SQL/Lakeview and tenant validation is pending.

**Consequences:** The product boundary is Databricks-centric for now, while contracts and SQL remain intentionally portable where practical.

### Decision 2: Incremental merge by product key and source watermark

| Attribute | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |

**Context:** Replays must not duplicate facts, and operational refresh should meet a 15-minute target after evidence generation.

**Choice:** Every product declares a business key and watermark; source rows are deduplicated with latest-watermark wins, then merged into Gold.

**Rationale:** It matches the KB incremental-loading pattern and supports deterministic replay, bounded scans and recovery evidence.

**Alternatives Rejected:** Full refresh — rejected because it increases cost and hides replay correctness; append-only — rejected because it cannot correct late or replayed records.

**Consequences:** Source contracts must provide stable keys and timestamps; missing keys fail the quality gate.

### Decision 3: Strict Gold quality gates block publication

| Attribute | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |

**Context:** Dashboards must not display an approved product containing null keys, duplicate business keys or stale data.

**Choice:** Gold builds fail before view publication when critical gates fail; failures emit structured evidence and do not replace the last approved view.

**Rationale:** The KB Gold aggregation pattern uses strict expectations for business-ready data, and Fase 6 requires explicit failure/skip reason codes.

**Alternatives Rejected:** Warn-and-publish — rejected for critical keys and contracts; silent quarantine — rejected because consumers need visible state.

**Consequences:** A failed run leaves the prior approved version intact and requires remediation/replay.

### Decision 4: External publication requires two gates

| Attribute | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |

**Context:** The repository may not have a workspace, warehouse or budget authorization.

**Choice:** Publication requires `--external`, complete capability inventory and an allowlisted test resource. Missing configuration yields `SKIP_WITH_REASON`.

**Rationale:** It preserves zero-cost local operation and prevents an implementation test from mutating cloud resources.

**Alternatives Rejected:** Auto-provision — rejected due to cost and permissions; treating local SQL as external proof — rejected for auditability.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---:|---|---|---|---|---|
| 1 | `pipelines/gold/__init__.py` | Create | Gold package boundary | @lakeflow-specialist | None |
| 2 | `pipelines/gold/config/gold_config.yaml` | Create | Products, SLAs and keys | @data-platform-engineer | None |
| 3 | `pipelines/gold/contracts/metric_registry.yaml` | Create | Versioned metric formulas | @data-contracts-engineer | 2 |
| 4 | `pipelines/gold/contracts/gold_products.yaml` | Create | Product grains and schema metadata | @data-contracts-engineer | 2 |
| 5 | `pipelines/gold/common/keys.py` | Create | Stable key and deduplication helpers | @databricks-spark-expert | 2 |
| 6 | `pipelines/gold/common/quality.py` | Create | Local quality gate facade | @data-quality-analyst | 3, 4 |
| 7 | `pipelines/gold/common/metrics.py` | Create | Metric calculation and versioning | @data-modeling specialist | 3 |
| 8 | `pipelines/gold/jobs/build_products.py` | Create | Deterministic local Gold build | @databricks-spark-expert | 5, 6, 7 |
| 9 | `pipelines/gold/jobs/publish_databricks.py` | Create | Opt-in SQL/Lakeview publication | @databricks-sql-expert | 4, 8 |
| 10 | `pipelines/gold/sql/market_insights.sql` | Create | Market/insights Gold model | @databricks-sql-expert | 3, 4 |
| 11 | `pipelines/gold/sql/lost_sales.sql` | Create | Lost sales Gold model | @databricks-sql-expert | 3, 4 |
| 12 | `pipelines/gold/sql/finops_costs.sql` | Create | Cost/anomaly Gold model | @databricks-sql-expert | 3, 4 |
| 13 | `pipelines/gold/sql/platform_health.sql` | Create | Evidence/observability Gold model | @databricks-sql-expert | 3, 4 |
| 14 | `pipelines/gold/sql/views/executive.sql` | Create | Executive semantic view | @databricks-sql-expert | 10–13 |
| 15 | `pipelines/gold/sql/views/operational.sql` | Create | Operational semantic view | @databricks-sql-expert | 10–13 |
| 16 | `pipelines/gold/dags/dag_build_gold.py` | Create | Airflow orchestration | @airflow-specialist | 8, 9 |
| 17 | `pipelines/gold/dashboards/executive.lakeview.json` | Create | Executive dashboard manifest | @databricks-sql-expert | 14 |
| 18 | `pipelines/gold/dashboards/operational.lakeview.json` | Create | Operational dashboard manifest | @databricks-sql-expert | 15 |
| 19 | `pipelines/gold/requirements.txt` | Create | Isolated dependencies | (general) | None |
| 20 | `pipelines/gold/tests/test_keys.py` | Create | Replay and key tests | @test-generator | 5 |
| 21 | `pipelines/gold/tests/test_quality.py` | Create | Quality gate tests | @data-quality-analyst | 6 |
| 22 | `pipelines/gold/tests/test_metrics.py` | Create | Formula and registry tests | @test-generator | 7 |
| 23 | `pipelines/gold/tests/test_build_products.py` | Create | Four product fixture tests | @test-generator | 8 |
| 24 | `pipelines/gold/tests/test_publish.py` | Create | External precondition tests | @databricks-sql-expert | 9 |
| 25 | `pipelines/gold/tests/test_dags_integrity.py` | Create | DagBag integrity | @airflow-specialist | 16 |
| 26 | `tests/gold/test_contracts.py` | Create | Contract/schema validation | @data-contracts-engineer | 3, 4 |
| 27 | `tests/gold/test_acceptance.py` | Create | DEFINE acceptance coverage | @test-generator | 20–25 |
| 28 | `docs/gold/PRODUCTS.md` | Create | Product and metric catalog | @code-documenter | 3, 4 |
| 29 | `docs/gold/LAKEVIEW.md` | Create | Publication and dashboard guide | @databricks-sql-expert | 17, 18 |
| 30 | `.github/workflows/gold-quality.yml` | Create | Gold domain CI matrix | @ci-cd-specialist | 19–27 |
| 31 | `docker-compose.local.yml` | Modify | Add optional Gold fixture runner only | (general) | 8 |
| 32 | `pyproject.toml` | Modify | Gold test markers/config | (general) | 20–27 |
| 33 | `.gitignore` | Modify | Generated Gold artifacts | (general) | 8 |

**Total Files:** 33

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|---|---|---|
| @lakeflow-specialist | 1 | Lakeflow/Delta Gold package patterns |
| @data-platform-engineer | 2 | Platform configuration and ownership |
| @data-contracts-engineer | 3, 4, 26 | Contract schema and data product metadata |
| @databricks-spark-expert | 5, 8 | Incremental merge and Delta execution |
| @data-quality-analyst | 6, 21 | Quality dimensions and gates |
| @databricks-sql-expert | 9–15, 17, 18, 24, 29 | Databricks SQL and Lakeview interfaces |
| @airflow-specialist | 16, 25 | Airflow 3 orchestration and DagBag |
| @test-generator | 20, 22, 23, 27 | Fixture and acceptance test generation |
| @ci-cd-specialist | 30 | Domain CI matrix and artifacts |
| @code-documenter | 28 | Product catalog and operator documentation |
| (general) | 19, 31–33 | Small dependency/config changes without a narrower specialist |

**Agent Discovery:** Scanned `.claude/agents/**/*.md`; matched by file type, purpose, path and KB domain.

---

## Code Patterns

### Pattern 1: Deterministic keyed incremental merge

```python
from collections.abc import Iterable


def latest_by_key(records: Iterable[dict], keys: tuple[str, ...], watermark: str) -> list[dict]:
    selected: dict[tuple[object, ...], dict] = {}
    for record in records:
        if any(record.get(key) is None for key in keys):
            raise ValueError("Gold business keys cannot be null")
        key = tuple(record[key] for key in keys)
        previous = selected.get(key)
        if previous is None or record[watermark] > previous[watermark]:
            selected[key] = record
    return list(selected.values())
```

This adapts the KB medallion incremental-loading pattern for local fixtures. Databricks execution uses the same key/watermark contract with `MERGE`.

### Pattern 2: Strict quality gate before publication

```python
def require_quality(rows: list[dict], key: str, required: tuple[str, ...]) -> None:
    if any(row.get(key) is None for row in rows):
        raise ValueError("QUALITY_FAILED:NULL_PRIMARY_KEY")
    if len({row[key] for row in rows}) != len(rows):
        raise ValueError("QUALITY_FAILED:DUPLICATE_BUSINESS_KEY")
    if any(any(row.get(column) is None for column in required) for row in rows):
        raise ValueError("QUALITY_FAILED:REQUIRED_COLUMN_NULL")
```

Critical Gold rules fail closed. Failure writes evidence and preserves the last approved version.

### Pattern 3: Versioned metric definition

```yaml
metric_id: lost_sales_value
version: 1
owner: analytics
grain: region, event_date
source_product: gold_lost_sales
formula: sum(lost_value)
unit: currency
tests: [not_null, non_negative, freshness_15m]
```

### Pattern 4: Safe external publication

```text
--external flag present
AND capability inventory configured
AND target resource in allowlist
AND Gold quality evidence is PASS/current
    -> publish and write evidence
otherwise
    -> SKIP_WITH_REASON, no cloud mutation
```

### Pattern 5: Databricks SQL Gold materialized view

```sql
CREATE OR REPLACE MATERIALIZED VIEW gold.market_insights_daily
COMMENT 'Governed daily market and insight KPIs'
TBLPROPERTIES ('quality' = 'gold', 'contract_version' = '1')
AS
SELECT event_date, source_class, SUM(metric_value) AS total_value,
       COUNT(*) AS metric_count, MAX(_updated_at) AS source_watermark
FROM silver.market_insights
GROUP BY event_date, source_class;
```

---

## Data Flow

```text
1. Load Gold contracts, metric registry and product config.
   |
   ▼
2. Read Silver, insights, FinOps and Fase 6 evidence by watermark.
   |
   ▼
3. Deduplicate by declared business key and latest source watermark.
   |
   ▼
4. Apply strict key, schema, completeness, volume and freshness gates.
   |
   ▼
5. Merge approved records into four Gold Delta products.
   |
   ▼
6. Generate semantic executive/operational views and validation evidence.
   |
   ▼
7. If external preconditions pass, publish Lakeview manifests; otherwise skip safely.
```

---

## Integration Points

| External System | Integration Type | Authentication |
|---|---|---|
| Databricks SQL/Delta | SQL connector/SDK | Workspace host/token or service principal, opt-in |
| Unity Catalog | Catalog metadata/API | Same Databricks identity |
| Airflow 3 | DAG/TaskFlow | Existing local Airflow connection |
| Fase 6 validation | JSON evidence and shared registry | Local filesystem/artifact reference |
| Lakeview | Dashboard API/manifest | Databricks identity, allowlisted workspace |

No integration creates a workspace, warehouse, catalog, dashboard or permission unless `--external` and capability-specific configuration are both present.

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|---|---|---|---|---|
| Unit | Key, deduplication, metric formulas, quality gates | `pipelines/gold/tests/test_keys.py`, `test_metrics.py`, `test_quality.py` | pytest | 100% critical rules |
| Contract | Product/metric YAML and JSON schema | `tests/gold/test_contracts.py` | pytest + PyYAML/jsonschema | All products and metrics |
| Fixture integration | Four Gold builds and replay | `test_build_products.py`, `test_acceptance.py` | pytest | AT-001–AT-007, AT-011–AT-012 |
| External precondition | Missing credentials, disabled flag, allowlist | `test_publish.py` | pytest mocks | AT-008–AT-009 |
| DagBag | Gold DAG imports and IDs | `test_dags_integrity.py`, `gold-quality.yml` | Airflow 3.0 container | Zero import errors |
| SQL validation | Databricks SQL syntax and views | CI optional workspace job | Databricks SQL | All model/view files |
| E2E | Gold → Lakeview | Manual/dispatch with test workspace | Airflow + Databricks | AT-009, external only |

Every DEFINE acceptance test is mapped to at least one test row. External tests are skipped with a reason when no configured workspace exists.

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|---|---|---|
| Null/duplicate key | Fail quality gate, preserve last approved product, emit reason code | No |
| Contract/schema mismatch | Reject publication, emit evidence with offending contract reference | No; requires change |
| Stale source | Mark product `STALE`, alert operational view, do not claim freshness | After source recovery |
| Databricks timeout | Bounded retry with correlation ID and checkpoint preservation | Yes, max 3 |
| SQL warehouse unavailable | External infrastructure failure evidence; keep local result | Yes, bounded |
| Missing credentials | `SKIP_WITH_REASON:MISSING_CREDENTIAL` | No |
| Duplicate replay | Keyed merge/idempotent update | Safe replay |
| Lakeview API 429 | Honor Retry-After and avoid duplicate dashboard mutation | Yes, bounded |

---

## Configuration

| Config Key | Type | Default | Description |
|---|---|---|---|
| `GOLD_ENVIRONMENT` | string | `local` | Environment label in evidence |
| `GOLD_CATALOG` | string | `automesh` | Databricks catalog when external |
| `GOLD_SCHEMA` | string | `gold` | Product schema when external |
| `GOLD_LOOKBACK_DAYS` | int | `2` | Late-arrival lookback for incremental builds |
| `GOLD_FRESHNESS_MINUTES` | int | `15` | Operational freshness SLA |
| `GOLD_EXTERNAL_ENABLED` | bool | `false` | Requires explicit CLI flag as second gate |
| `GOLD_ALLOWLIST_RESOURCE` | string | empty | Named test warehouse/workspace resource |
| `DATABRICKS_SQL_WAREHOUSE_ID` | string | empty | Required only for external SQL execution |
| `GOLD_PUBLICATION_TIMEOUT_SECONDS` | int | `300` | Bounded API/SQL timeout |

---

## Security Considerations

- Never place Databricks tokens, service principal secrets, recipient IDs or raw sensitive columns in Gold logs, inventory or evidence.
- Apply Unity Catalog ownership, catalog/schema permissions and column classification before external publication.
- Executive views must exclude or aggregate sensitive source columns; operational views expose references and reason codes, not secret values.
- Publication is deny-by-default and requires explicit flag, configured capability and allowlisted resource.
- SQL identifiers come from validated configuration, never raw user input; metric formulas come from versioned registry files.

---

## Observability

| Aspect | Implementation |
|---|---|
| Logging | Existing `pipelines.observability.logging` JSON formatter with product, run, correlation and reason fields |
| Metrics | Existing bounded `Metrics` facade: `gold.build.records`, `gold.quality.failures`, `gold.refresh.age`, `gold.publication.result` |
| Tracing | `bind_context` around source read, build, quality and publication stages |
| Evidence | Fase 6 `Evidence` records per product/gate with artifact references and expiry |
| Dashboard health | Operational view exposes source watermark, last successful build and stale status |

---

## Pipeline Architecture (if applicable)

### DAG Diagram

```text
[Silver + Insights + FinOps + Evidence]
             | extract by watermark
             ▼
       [Gold build tasks]
             | dedup + merge
             ▼
       [Quality gate]
        | pass       | fail
        ▼            ▼
[Gold Delta/views] [Evidence + alert]
        |
        ▼
[Lakeview manifests/publication adapter]
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|---|---|---|---|
| `gold_market_insights_daily` | `event_date` | Daily | Time-series and bounded refresh |
| `gold_lost_sales_daily` | `event_date` | Daily | Executive trend queries |
| `gold_finops_costs` | `usage_date` | Daily | Cost windows and anomaly scans |
| `gold_platform_health` | `observed_at` | Daily | Operational freshness and retention |

Small fixture tables remain unpartitioned locally. Databricks physical optimization is deferred until measured query volume exists.

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|---|---|---|---|
| Market insights | watermark + MERGE | `source_event_id` | 2 days |
| Lost sales | watermark + MERGE | `sale_id` | 2 days |
| FinOps costs | window rebuild + MERGE | `usage_id` or `job_name, usage_date` | 2 days |
| Platform health | append by event + dedup | `event_id` | 2 days |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|---|---|---|
| New nullable column | Add to contract as backward-compatible, update views after validation | Revert contract/view |
| New required column | Two-step contract: observe then enforce | Restore prior contract |
| Type change | Block publication; dual-version migration | Keep prior Gold version |
| Column removal | Deprecate for one release and remove from views after consumer check | Re-add prior projection |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|---|---|---:|---|
| Primary key not null | Local/SQL assertion | 100% | Block build |
| Business key unique | Local/SQL assertion | 100% | Block merge |
| Required metric fields | Contract validator | 100% | Block publication |
| Row count sanity | Quality facade | Within configured 0.5x–2.0x baseline | Alert and hold view |
| Freshness | Watermark comparison | ≤ 15 min operational | Mark `STALE` and alert |
| Metric formula | Registry tests | 100% fixture match | Block dashboard release |
| Sensitive-column scan | Contract/security test | 0 unapproved fields | Block publication |

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-17 | design-agent | Initial Gold products, SQL/Lakeview, quality and publication design |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_FASE7_GOLD_BI_DATABRICKS.md`
