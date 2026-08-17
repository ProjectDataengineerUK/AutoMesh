# Incident Response Patterns for Data Platforms

> **Purpose**: Runbook patterns for diagnosing and resolving data pipeline incidents on Databricks and Fabric.
> **Sentinel integration**: These patterns feed the Sentinel analyzer and interpreter crews.

---

## Incident Taxonomy

| Severity | Description | Response SLO | Example |
|----------|-------------|-------------|---------|
| **P0 — Critical** | Data loss or total pipeline failure in production | 15 min acknowledge, 1h resolve | Bronze ingestion stopped, Gold tables not updating |
| **P1 — High** | SLO breach persisting >30 min or data quality failure | 30 min acknowledge, 4h resolve | Silver quality SLO < 95%, freshness >60 min stale |
| **P2 — Medium** | Degraded performance, partial failures, non-critical tables | Next business day | Non-critical Gold table stale, test environment failures |
| **P3 — Low** | Cosmetic issues, documentation gaps, non-impacting anomalies | Sprint backlog | Warning alerts without downstream impact |

---

## Sentinel Detection Flow

```
Watcher signals → Analyzer diagnosis → Interpreter context → Actionable runbook
     ↓                    ↓                    ↓
 freshness miss      z-score anomaly      pattern matched → this file
 quality violation   trend regression     probable cause → next steps
 job failure         diff from baseline   confidence score → escalation
```

---

## Runbook: Pipeline Job Failure (Databricks)

### 1. Triage

```sql
-- Find failed runs in the last 24h
SELECT run_id, job_name, status, error_message,
       start_time, end_time,
       DATEDIFF(SECOND, start_time, end_time) AS duration_s
FROM system.lakeflow.job_run_timeline
WHERE status = 'FAILED'
  AND start_time >= CURRENT_TIMESTAMP - INTERVAL 1 DAY
ORDER BY start_time DESC;
```

### 2. Classify failure

| Error pattern | Likely cause | Action |
|--------------|-------------|--------|
| `AnalysisException: Table not found` | Schema drift or dropped table | Check source schema, SYNC Unity Catalog |
| `OutOfMemoryError` | Data volume spike | Increase cluster size or add partition |
| `SparkException: Job aborted` | Executor timeout | Check cluster logs, increase timeout |
| `delta.exceptions.ConcurrentAppendException` | Write conflict | Add retry with backoff |
| `FileNotFoundException` | Source file not landed | Check upstream pipeline / ingestion |

### 3. Rollback pattern (Delta Lake)

```sql
-- Check table version history before rollback
DESCRIBE HISTORY catalog.silver.orders LIMIT 10;

-- Rollback to last known good version
RESTORE TABLE catalog.silver.orders TO VERSION AS OF 42;
```

---

## Runbook: Data Quality Incident

### Detection

```sql
-- Quality degradation in Silver (last 7 days trend)
SELECT
  DATE(event_time) AS date,
  rule_name,
  passed_count,
  failed_count,
  ROUND(passed_count * 100.0 / (passed_count + failed_count), 2) AS pass_rate_pct
FROM system.data_quality.validation_results
WHERE table_name = 'silver.orders'
ORDER BY date DESC, pass_rate_pct ASC;
```

### Quarantine pattern

```python
# Isolate failing records — quarantine-first before remediation
df_good = df.filter(col("validation_status") == "PASS")
df_bad  = df.filter(col("validation_status") == "FAIL")

# Write bad records to quarantine (never drop)
df_bad.write.mode("append").saveAsTable("quarantine.silver_orders_failures")
df_good.write.mode("append").saveAsTable("silver.orders")
```

---

## Runbook: Freshness SLO Breach

```sql
-- Identify which tables are stale
SELECT table_name, last_modified,
       DATEDIFF(MINUTE, last_modified, CURRENT_TIMESTAMP) AS minutes_stale
FROM system.information_schema.tables
WHERE table_schema IN ('silver', 'gold')
  AND DATEDIFF(MINUTE, last_modified, CURRENT_TIMESTAMP) > 30
ORDER BY minutes_stale DESC;
```

**Resolution steps:**
1. Check upstream job status → is Bronze updated?
2. Check cluster availability → is the Silver job queued or failed?
3. Trigger manual backfill if source data is available but job failed
4. Alert downstream consumers if Gold SLO will be breached

---

## Escalation Matrix

| Signal | Route to |
|--------|---------|
| Databricks Jobs failure | `@databricks-spark-expert` (pipeline fix) |
| Data quality violation | `@data-quality-analyst` (agentspec) |
| Access/permission error | `@data-platform-security` |
| Unity Catalog schema drift | `@databricks-sql-expert` |
| Fabric pipeline failure | `@fabric-pipeline-expert` |
| LGPD/GDPR exposure risk | `@data-governance-auditor` |
| Multi-domain impact | `@doma-supervisor` → `/party` |
