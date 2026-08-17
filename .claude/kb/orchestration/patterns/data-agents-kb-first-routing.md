# Data Agents KB-First Routing

## Purpose

Preserve the useful `data-agents` routing principle: pick the KB first, then
the specialist role, then the implementation procedure.

## Routing Pattern

1. Classify the task shape.
2. Load the relevant KB domain.
3. Select the specialist role.
4. Confirm platform and criticality.
5. Produce or update the durable artifact.
6. Run the validation loop for that artifact type.

## Platform Routing

| Task Shape | AgentCodex KB | Preferred Role |
|---|---|---|
| Databricks jobs, bundles, Unity Catalog | `platforms/databricks` | `databricks-architect` |
| Fabric lakehouse, Direct Lake, RTI | `microsoft-fabric` | `fabric-architect` |
| Cross-platform Databricks/Fabric | `lakehouse`, `platforms/databricks`, `microsoft-fabric` | `data-platform-engineer` |
| Data quality, drift, profiling, SLA | `data-quality` | `data-quality-analyst` |
| Governance, PII, audit, access | `controls/governance`, `access-control`, `lineage` | `data-governance-architect` |
| Semantic model or metric layer | `data-modeling`, `dbt`, platform KB | `schema-designer` or `dbt-specialist` |
| Relational migration | `lakehouse/patterns/relational-migration.md` | `migrate` command plus `data-platform-engineer` |

## Source Notes

- Enriched from `data-agents/kb/task_routing.md`
