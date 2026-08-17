# Cost Management Patterns for Databricks and Fabric

> **Purpose**: Cost modeling, monitoring, and optimization patterns for data platform workloads.
> **Platforms**: Databricks (DBUs), Microsoft Fabric (CUs — Capacity Units).

---

## Cost Drivers

| Driver | Databricks | Fabric |
|--------|-----------|--------|
| Compute | DBU/hour by node type | CU consumption per workload |
| Storage | ADLS Gen2 ($/GB/month) | OneLake ($/GB/month) |
| SQL queries | SQL Warehouse DBUs | Fabric SQL Analytics (CUs) |
| Streaming | Jobs cluster DBUs | Eventstream (CUs) |
| AI/ML | ML cluster DBUs + model serving | Fabric Copilot (CUs) |

---

## Cost Monitoring Queries

### Databricks — DBU consumption by workload

```sql
-- Top cost drivers (last 30 days)
SELECT
  usage_metadata.job_name AS workload,
  SUM(usage_quantity) AS total_dbus,
  ROUND(SUM(usage_quantity) * 0.40, 2) AS estimated_cost_usd,
  COUNT(DISTINCT usage_date) AS active_days
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE - INTERVAL 30 DAYS
  AND billing_origin_product IN ('JOBS', 'DLT', 'SQL')
GROUP BY 1
ORDER BY total_dbus DESC
LIMIT 20;
```

### Databricks — Identify idle clusters

```sql
SELECT cluster_id, cluster_name, cluster_source,
       MAX(DATEDIFF(MINUTE, last_activity_time, CURRENT_TIMESTAMP)) AS idle_minutes
FROM system.compute.clusters
WHERE state = 'RUNNING'
GROUP BY 1, 2, 3
HAVING idle_minutes > 60
ORDER BY idle_minutes DESC;
```

### Fabric — Capacity utilization trend

```sql
-- Monitor Fabric CU consumption (Capacity Metrics App data)
SELECT
  DATE_TRUNC('hour', TimePoint) AS hour,
  ItemKind,
  SUM(CUs) AS total_cus,
  MAX(ThrottlingStarted) AS was_throttled
FROM capacitymetrics.CapacityUsage
WHERE TimePoint >= DATEADD(DAY, -7, GETDATE())
GROUP BY 1, 2
ORDER BY 1 DESC, total_cus DESC;
```

---

## Cost Optimization Patterns

### Databricks

| Pattern | Impact | Implementation |
|---------|--------|---------------|
| Auto-terminate clusters | High | Set `autotermination_minutes: 20` on interactive clusters |
| Spot/Preemptible nodes | Medium | Use worker node type = spot for Jobs clusters |
| Photon for SQL | High | Enable Photon on SQL Warehouse — reduces query time = fewer DBUs |
| OPTIMIZE + ZORDER | Medium | Run weekly on high-query tables to reduce scan costs |
| Cluster sizing | High | Match node count to actual parallelism — avoid over-provisioning |
| Delta caching | Medium | Enable on repeated scan workloads |

```sql
-- Weekly OPTIMIZE to reduce small file tax
OPTIMIZE catalog.silver.orders ZORDER BY (order_date, customer_id);
VACUUM catalog.silver.orders RETAIN 168 HOURS;
```

### Fabric

| Pattern | Impact | Implementation |
|---------|--------|---------------|
| Pause capacity off-hours | High | Fabric Admin Portal → schedule capacity pause |
| Direct Lake over Import | High | Avoids dual storage cost for Power BI datasets |
| Partition Gold tables | Medium | Reduces T-SQL scan cost on Fabric SQL Analytics |
| Eventstream sizing | Medium | Right-size stream throughput to avoid CU overage |

---

## Cost Alerting

```python
# Alert when weekly DBU spend exceeds budget
import requests

def check_dbu_budget(workspace_url: str, token: str, weekly_budget_dbus: float):
    resp = requests.get(
        f"{workspace_url}/api/2.0/usage/download",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_month": "2026-01", "personal_data": "false"}
    )
    # Compare total_dbus to budget
    # Trigger Sentinel quality watcher if breached
```

---

## Sentinel Integration

Cost signals feed the Sentinel watcher crew:
- **pipeline watcher** → monitors job duration anomalies (cost spike indicator)
- **quality watcher** → monitors OPTIMIZE run schedules (missing = rising small file tax)
- Output → `operations/cost/cost-model.md` in project feature directory
