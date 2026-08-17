# Databricks Quick Reference

## Purpose

Fast decision reference for Databricks work in AgentCodex.

## Decision Matrix

| Need | Prefer | Escalate To |
|---|---|---|
| Workspace, catalog, jobs, bundles, or platform boundaries | `databricks-architect` | `data-platform-engineer` |
| Lakeflow or DLT-style pipeline design | Spark Declarative Pipelines | `lakeflow-architect`, `lakeflow-specialist` |
| Spark code and runtime behavior | Spark role plus Databricks constraints | `spark-engineer` |
| RAG, Vector Search, Model Serving, AI Functions | Databricks AI surface | `mosaic-ai-engineer`, `genai-architect` |
| SQL warehouse, dashboards, DBSQL queries | Serverless SQL warehouse where available | `sql-optimizer`, `data-observability-engineer` |
| Governance, volumes, grants, lineage, audit | Unity Catalog + system tables | `data-governance-architect`, `platform-access-engineer` |
| CI/CD and resource deployment | Databricks Asset Bundles | `ci-cd-specialist` |

## High-Value Rules

1. Use three-level Unity Catalog names: `catalog.schema.object`.
2. Store non-tabular files under Unity Catalog Volumes, not DBFS root.
3. Prefer file-based Databricks Asset Bundles over manual workspace drift.
4. Use job clusters or serverless for production workflows; avoid interactive clusters for scheduled pipelines.
5. For pipeline tables, prefer `CLUSTER BY` or `CLUSTER BY (AUTO)` over new `ZORDER` usage.
6. For dashboards, test every SQL query before publishing the dashboard definition.
7. For AI Functions, prefer task-specific functions before generic `ai_query`.
8. For Vector Search, choose endpoint/index type before writing ingestion code.
9. For system tables, always filter by date where possible.
10. For long-running or streaming jobs, define health rules, retries, timeout, and alerting.

## Common Gotchas

| Area | Gotcha | Safer Default |
|---|---|---|
| Unity Catalog | Granting `SELECT` without `USE CATALOG` and `USE SCHEMA` still blocks discovery | Grant parent scopes first |
| Volumes | `/Volumes/...` paths are case-sensitive | Normalize catalog/schema/volume naming |
| Bundles | Paths in `resources/*.yml` resolve relative to the resource file | Use `../src/...` from `resources/*.yml` |
| Jobs | Timeout is task-level, not only job-level | Set `timeout_seconds` on long tasks |
| Jobs | Duplicate manual runs can happen | Use `idempotency_token` for `run_now` |
| SDP/Lakeflow | Legacy `import dlt` examples may be stale in docs/prompts | Prefer current Spark Declarative Pipelines terminology |
| AI/BI | Legacy dashboards are not the target for new work | Use AI/BI dashboards |
| Vector Search | Storage-optimized indexes have different sync/capacity tradeoffs | Pick endpoint type from latency and scale needs |

## Local References

- `concepts/unity-catalog-operations.md`
- `concepts/compute-and-jobs.md`
- `patterns/databricks-asset-bundles.md`
- `patterns/spark-declarative-pipelines.md`
- `concepts/databricks-ai-surface.md`
