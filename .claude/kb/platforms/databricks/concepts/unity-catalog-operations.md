# Unity Catalog Operations

## Purpose

Normalize the Databricks governance surface from `data-agents` into AgentCodex
KB guidance.

## Core Model

Unity Catalog work should be expressed with explicit three-level names:

```text
catalog.schema.table
catalog.schema.volume
catalog.schema.function
```

Avoid implicit table names that can drift into legacy metastore behavior.

## Grant Order

Grant parent scopes before object permissions:

```sql
GRANT USE CATALOG ON CATALOG main TO `data_engineers`;
GRANT USE SCHEMA ON SCHEMA main.analytics TO `data_engineers`;
GRANT SELECT ON TABLE main.analytics.orders TO `data_engineers`;
```

For volumes:

```sql
GRANT USE CATALOG ON CATALOG main TO `data_engineers`;
GRANT USE SCHEMA ON SCHEMA main.raw TO `data_engineers`;
GRANT READ VOLUME ON VOLUME main.raw.landing TO `data_engineers`;
```

## Volumes

Use Unity Catalog Volumes for non-tabular assets such as JSON, CSV, PDFs,
images, model inputs, generated reports, and RAG documents.

```text
/Volumes/catalog/schema/volume_name/path/to/file
```

Rules:

- Treat `/Volumes/...` as case-sensitive.
- Prefer Volumes over DBFS root or mounts for new governed work.
- Use volume permissions instead of table permissions for file access.

## System Tables

System tables are the first audit and observability source for Databricks work.
Date filters are required for large tables.

| Table | Use |
|---|---|
| `system.access.audit` | permission changes, deletes, access events |
| `system.access.table_lineage` | table-level lineage |
| `system.access.column_lineage` | column-level lineage where available |
| `system.billing.usage` | DBU and SKU usage |
| `system.compute.*` | compute and warehouse usage |
| `system.lakeflow.*` | Lakeflow jobs and pipeline run analysis where available |

Example access grants:

```sql
GRANT USE CATALOG ON CATALOG system TO `data_engineers`;
GRANT USE SCHEMA ON SCHEMA system.access TO `data_engineers`;
GRANT SELECT ON SCHEMA system.access TO `data_engineers`;
```

Example lineage query:

```sql
SELECT DISTINCT source_table_full_name, source_column_name
FROM system.access.table_lineage
WHERE target_table_full_name = 'main.analytics.orders_gold'
  AND event_date >= current_date() - 7;
```

Example audit query:

```sql
SELECT event_time, user_identity.email, action_name, request_params
FROM system.access.audit
WHERE event_date >= current_date() - 30
  AND (action_name LIKE '%GRANT%' OR action_name LIKE '%REVOKE%')
ORDER BY event_time DESC
LIMIT 100;
```

## Review Checklist

- [ ] All persistent objects use `catalog.schema.object`.
- [ ] Parent `USE CATALOG` and `USE SCHEMA` grants are present.
- [ ] Volumes are used for files.
- [ ] System table queries include bounded date filters.
- [ ] Lineage and audit access is explicitly granted to operating groups.
- [ ] Access-control changes are reviewed by `platform-access-engineer` or `data-governance-architect`.

## Source Notes

- Enriched from `data-agents/kb/databricks/concepts/unity-catalog-concepts.md`
- Enriched from `data-agents/skills/databricks/databricks-unity-catalog/`
