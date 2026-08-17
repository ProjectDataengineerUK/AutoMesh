# Spark Declarative Pipelines

## Purpose

Capture modern Databricks pipeline guidance from `data-agents`, normalized for
AgentCodex Lakeflow and Spark roles.

## Naming

Databricks material in `data-agents` treats Delta Live Tables as renamed into
Lakeflow Spark Declarative Pipelines. Existing `dlt` code can still exist, but
new documentation and prompts should prefer the current Databricks naming.

Use this role split:

- architecture: `lakeflow-architect`
- implementation details: `lakeflow-specialist` or `lakeflow-pipeline-builder`
- Spark runtime issues: `spark-engineer` or `spark-troubleshooter`

## SQL Table Types

| Type | Use |
|---|---|
| Streaming table | incremental ingestion and transformations |
| Materialized view | stored aggregate or reporting table with incremental refresh |
| View | persisted Unity Catalog view without stored data |
| Temporary view | pipeline-scoped intermediate transformation |

## Python Guidance

For new Python examples, prefer:

```python
from pyspark import pipelines as dp
```

Avoid adding new examples that require `import dlt` unless documenting legacy
compatibility.

## Data Quality

Use expectations at the table boundary:

```sql
CREATE OR REFRESH STREAMING TABLE silver_orders (
  CONSTRAINT valid_amount EXPECT (amount > 0) ON VIOLATION DROP ROW,
  CONSTRAINT valid_order EXPECT (order_id IS NOT NULL) ON VIOLATION FAIL UPDATE
)
AS SELECT * FROM STREAM bronze_orders;
```

## CDC And SCD

AUTO CDC is the preferred high-level pattern when implementing Type 1 or Type 2
dimension maintenance inside managed pipelines.

Key rules:

- Use stable business keys.
- Sequence by event timestamp or source sequence.
- Put delete handling before sequence logic where syntax requires it.
- Track SCD Type 2 only for attributes where history matters.

## Performance Defaults

Prefer Liquid Clustering style patterns for new tables:

```sql
CREATE OR REFRESH STREAMING TABLE silver_orders
CLUSTER BY (customer_id, order_date)
AS
SELECT * FROM STREAM bronze_orders;
```

Use `CLUSTER BY (AUTO)` when access patterns are not known yet.

Layer guidance:

| Layer | Good clustering keys |
|---|---|
| Bronze | event type, ingestion date |
| Silver | primary key, business date |
| Gold | dashboard/filter dimensions |

## Streaming Rules

- Use event time for business logic.
- Keep ingestion time for debugging.
- Bound stream-to-stream joins with time conditions.
- Use checkpoint and state retention deliberately for stateful operations.
- Treat late-arriving data as a design requirement, not an edge case.

## Review Checklist

- [ ] Pipeline naming uses Lakeflow/SDP terminology for new docs.
- [ ] Unity Catalog target catalog/schema is explicit.
- [ ] Streaming joins are bounded by time.
- [ ] Expectations exist for critical quality rules.
- [ ] CDC/SCD keys and sequence columns are explicit.
- [ ] `CLUSTER BY` strategy is justified.
- [ ] Deployment path is bundle-based where possible.

## Source Notes

- Enriched from `data-agents/skills/databricks/databricks-spark-declarative-pipelines/`
- Enriched from `data-agents/skills/databricks/databricks-spark-structured-streaming/`
