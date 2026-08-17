# Compute And Jobs

## Purpose

Capture Databricks compute and job orchestration decisions that should inform
AgentCodex design, build, and review steps.

## Compute Decision Matrix

| Workload | Prefer | Notes |
|---|---|---|
| Local PySpark development and tests | Databricks Connect | Good for fast dev feedback when compatible with runtime and Python version |
| SQL dashboards and BI queries | Serverless SQL warehouse | Keep dashboards off interactive clusters |
| Production ETL DAG | Job cluster or serverless task | Define task boundaries and retries |
| Exploratory notebooks | Interactive cluster | Require auto-termination and explicit user confirmation before startup |
| Heavy ML/batch task | Serverless compute or job cluster | Persist state through tables or volumes |
| Continuous tables/pipelines | Spark Declarative Pipelines | Avoid ad hoc notebooks for managed pipelines |

## Job Task Types

| Task Type | Use |
|---|---|
| `notebook_task` | Notebook execution, often for existing workspace workflows |
| `spark_python_task` | Python script execution without notebook semantics |
| `python_wheel_task` | Packaged Python entry points |
| `sql_task` | SQL query, file, dashboard, or alert refresh |
| `dbt_task` | dbt transformations |
| `pipeline_task` | Trigger managed pipeline execution |
| `run_job_task` | Compose jobs without duplicating task definitions |
| `for_each_task` | Parameterized fan-out patterns |

## Scheduling And Triggers

Use the simplest trigger that matches the business event:

| Trigger | Use |
|---|---|
| Cron schedule | Recurring business schedules |
| Periodic trigger | Simple fixed interval |
| File arrival trigger | Reacting to cloud object arrival |
| Table update trigger | Reacting to Unity Catalog table changes |
| Manual run | Ad hoc run with explicit `idempotency_token` |

## Reliability Defaults

For production jobs:

- define `max_retries`
- define `retry_on_timeout` for long external or compute-heavy steps
- define `timeout_seconds` per long task
- define failure notifications or webhook destinations
- define health rules for long-running or streaming workloads
- use idempotent task logic and idempotency tokens for manual `run_now`

## Run Conditions

`run_if` is evaluated after dependencies complete. Use explicit conditions for
recovery and cleanup paths.

| Condition | Use |
|---|---|
| `ALL_SUCCESS` | normal dependency success path |
| `ALL_DONE` | cleanup/reporting that should run after success or failure |
| `AT_LEAST_ONE_FAILED` | fallback or incident capture |
| `NONE_FAILED` | continue when dependencies succeeded or were skipped |

## Review Checklist

- [ ] Production workflows do not rely on interactive clusters.
- [ ] Interactive clusters have auto-termination.
- [ ] Each long task has timeout and retry policy.
- [ ] Failure notifications or webhooks are configured.
- [ ] Schedules and timezones are explicit.
- [ ] File/table triggers have underlying IAM/RBAC and UC access verified.
- [ ] Manual runs use `idempotency_token` where duplication matters.

## Source Notes

- Enriched from `data-agents/kb/databricks/concepts/compute-concepts.md`
- Enriched from `data-agents/kb/databricks/concepts/jobs-concepts.md`
- Enriched from `data-agents/skills/databricks/databricks-jobs/`
