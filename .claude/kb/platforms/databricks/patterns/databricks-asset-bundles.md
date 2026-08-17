# Databricks Asset Bundles

## Purpose

Use Databricks Asset Bundles as the default file-based deployment shape for
Databricks jobs, pipelines, dashboards, apps, and related resources.

## Project Shape

```text
project/
├── databricks.yml
├── resources/
│   ├── jobs.yml
│   ├── pipelines.yml
│   └── dashboards.yml
└── src/
    ├── notebooks/
    ├── dashboards/
    └── app/
```

## Path Resolution

Paths resolve from the file where they are declared.

| File | Use |
|---|---|
| `databricks.yml` | `./src/...` |
| `resources/*.yml` | `../src/...` |
| `resources/nested/*.yml` | `../../src/...` |

The common failure is using `./src/...` inside `resources/*.yml`, which points
to `resources/src/...`.

## Core Commands

```bash
databricks bundle validate
databricks bundle plan
databricks bundle deploy -t dev
databricks bundle deploy -t prod
databricks bundle run <resource_key> -t dev
```

## Resource Notes

| Resource | Notes |
|---|---|
| Jobs | use task-level retries, timeouts, and notifications |
| Pipelines | use catalog/schema variables and environment-specific targets |
| Dashboards | validate every SQL dataset before deployment |
| Apps | keep runtime env vars in app resource files, not hardcoded IDs |
| Alerts | verify schema because alert definitions differ from job definitions |
| Volumes | use grants, not generic workspace permissions |

## Minimal Target Pattern

```yaml
bundle:
  name: my-project

include:
  - resources/*.yml

variables:
  catalog:
    default: dev_catalog
  schema:
    default: dev_schema

targets:
  dev:
    default: true
    mode: development
    variables:
      catalog: dev_catalog
      schema: dev_schema

  prod:
    mode: production
    variables:
      catalog: prod_catalog
      schema: prod_schema
```

## Review Checklist

- [ ] `databricks bundle validate` is part of verification.
- [ ] `databricks bundle plan` is reviewed before production deploy.
- [ ] Dev/prod targets are explicit.
- [ ] Catalog and schema are variables, not hardcoded across files.
- [ ] Resource file paths are relative to the declaring file.
- [ ] Admin groups are not redundantly added to resource permissions.
- [ ] Dashboard SQL is tested before dashboard JSON is deployed.

## Source Notes

- Enriched from `data-agents/kb/databricks/concepts/bundles-concepts.md`
- Enriched from `data-agents/kb/databricks/patterns/cicd-patterns.md`
- Enriched from `data-agents/skills/databricks/databricks-bundles/`
