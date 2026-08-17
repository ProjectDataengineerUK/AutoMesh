# Data Agents Lineage Patterns

## Purpose

Represent lineage guidance from `data-agents` in AgentCodex's metadata domain.

## Required Lineage Coverage

- source system to Bronze
- Bronze to Silver transformations
- Silver to Gold/reporting transformations
- semantic model/report dependencies
- cross-platform handoffs such as shortcuts, mirroring, copied extracts, or open table interop

## Platform Sources

| Platform | Preferred Evidence |
|---|---|
| Databricks | system lineage tables, Unity Catalog object names, bundle/job definitions |
| Fabric | workspace lineage, OneLake artifacts, semantic model dependencies |
| dbt | manifest lineage and model DAG |
| Airflow/orchestration | DAG dependencies and task outputs |

## Review Checklist

- [ ] Gold table lineage is traceable to original source.
- [ ] Column-level lineage is documented for regulated or critical fields.
- [ ] Cross-platform movement states copy vs shortcut vs mirror vs shared format.
- [ ] Lineage evidence is reproducible by query, manifest, or documented command.
- [ ] Impact analysis exists before structural changes.

## Source Notes

- Enriched from `data-agents/kb/governance/concepts/lineage-concepts.md`
- Enriched from `data-agents/kb/governance/patterns/lineage-patterns.md`
