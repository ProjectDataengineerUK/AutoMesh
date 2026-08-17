# SLA / SLO Patterns for Data Pipelines

> **Purpose**: Define and enforce service level objectives for data pipelines on Databricks and Fabric.
> **Applies to**: pipeline freshness, quality gates, ingestion latency, transformation SLAs.

---

## Core Concepts

| Term | Definition |
|------|-----------|
| **SLO** | Target threshold (e.g., "Silver layer updated within 30min of Bronze arrival") |
| **SLA** | Contractual commitment derived from SLOs (agreed with consumers) |
| **Error Budget** | Allowable failure rate = 1 - SLO target (e.g., 99.5% → 0.5% budget) |
| **Freshness SLO** | Max acceptable age of data in a layer at any given time |
| **Quality SLO** | Min % of records passing validation rules |

---

## Standard SLO Tiers

### Data Platform SLOs (Databricks/Fabric)

| Layer | Freshness SLO | Quality SLO | Latency SLO |
|-------|--------------|-------------|-------------|
| Bronze (raw) | ≤ 15 min from source event | ≥ 95% parse success | ≤ 5 min landing |
| Silver (clean) | ≤ 30 min from Bronze | ≥ 99% validation pass | ≤ 10 min transform |
| Gold (aggregated) | ≤ 60 min from Silver | ≥ 99.5% referential integrity | ≤ 20 min aggregate |
| Semantic Layer | ≤ 4 hours from Gold | N/A | On-demand refresh |

---

## SLO Enforcement Patterns

### Freshness Check (Databricks — Unity Catalog)

```sql
-- Check if Silver layer is stale beyond SLO
SELECT
  table_name,
  last_modified,
  DATEDIFF(MINUTE, last_modified, CURRENT_TIMESTAMP) AS minutes_stale,
  CASE WHEN DATEDIFF(MINUTE, last_modified, CURRENT_TIMESTAMP) > 30
       THEN 'SLO_VIOLATED'
       ELSE 'OK'
  END AS freshness_status
FROM system.information_schema.tables
WHERE table_schema = 'silver'
ORDER BY minutes_stale DESC;
```

### Quality SLO Gate (dbt / Great Expectations pattern)

```yaml
# schema.yml — fail pipeline if quality SLO breached
models:
  - name: silver_orders
    tests:
      - dbt_utils.accepted_row_values:
          column_name: status
          values: ['pending', 'confirmed', 'shipped', 'cancelled']
      - not_null:
          column_name: order_id
          config:
            error_if: ">0.01"  # fail if >1% null (quality SLO: 99%)
```

### Alerting on SLO Breach (Databricks Jobs)

```python
# Fail job and trigger alert if freshness SLO breached
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient

def check_freshness_slo(table: str, max_minutes: int):
    w = WorkspaceClient()
    last_modified = w.tables.get(table).updated_at
    age = datetime.now() - last_modified
    if age > timedelta(minutes=max_minutes):
        raise ValueError(f"SLO BREACH: {table} is {age.seconds//60}min stale (SLO={max_minutes}min)")
```

---

## Error Budget Tracking

```sql
-- Weekly error budget consumption (Databricks system tables)
SELECT
  DATE_TRUNC('week', event_time) AS week,
  pipeline_name,
  COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failures,
  COUNT(*) AS total_runs,
  ROUND(1.0 - COUNT(CASE WHEN status = 'FAILED' THEN 1 END) * 1.0 / COUNT(*), 4) AS availability,
  ROUND(COUNT(CASE WHEN status = 'FAILED' THEN 1 END) * 1.0 / COUNT(*), 4) AS error_budget_consumed
FROM system.lakeflow.job_run_timeline
WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL 90 DAYS
GROUP BY 1, 2
ORDER BY error_budget_consumed DESC;
```

---

## Sentinel Integration

SLO breaches feed the Sentinel watcher crew:
- **pipeline watcher** → monitors freshness and schedule violations
- **quality watcher** → monitors validation pass rates vs SLO thresholds
- Output → `operations/observability/alerts.md` severity classification
