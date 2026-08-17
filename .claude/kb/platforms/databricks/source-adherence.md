# Data Agents Adherence Notes

## Purpose

Record the Databricks enrichment brought from the local `data-agents` material.

## Compared Sources

- `data-agents/kb/databricks/index.md`
- `data-agents/kb/databricks/concepts/`
- `data-agents/kb/databricks/patterns/`
- `data-agents/skills/databricks/`

## What Was Missing In AgentCodex

Before this pass, AgentCodex had only a high-level Databricks overview. The
following details were present in `data-agents` and are now represented in the
Databricks KB:

- Unity Catalog grant order, Volumes, and system table usage
- compute and job task decision matrix
- Databricks Asset Bundle path-resolution gotchas
- job schedules, triggers, retries, run conditions, and idempotency
- Spark Declarative Pipelines / Lakeflow naming and table patterns
- AUTO CDC, SCD, streaming join, and clustering guidance
- AI Functions, Agent Bricks, Genie, Vector Search, Model Serving, MLflow Evaluation, Apps, and Lakebase positioning

## Deliberately Not Ported Directly

- Claude-oriented skills as active runtime skills
- MCP tool names as required AgentCodex runtime dependencies
- UI-specific Chainlit behavior
- source examples that require live Databricks workspace credentials

## Next Candidates

If Databricks depth remains a priority, the next useful pass is to split this
domain into narrower KB pages:

- `concepts/vector-search.md`
- `concepts/model-serving.md`
- `concepts/mlflow-evaluation.md`
- `concepts/agent-bricks.md`
- `patterns/databricks-apps.md`
- `patterns/zerobus-ingest.md`
- `patterns/spark-python-data-source.md`
