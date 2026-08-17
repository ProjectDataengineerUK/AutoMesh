# Data Agents Governance Controls

## Purpose

Capture governance, PII, audit, and compliance patterns from `data-agents` in
AgentCodex's control layer.

## Access Rules

1. Grant access through groups, not individual users.
2. Apply least privilege at catalog, schema, table, volume, workspace, and item levels.
3. Require data owner approval before granting access to restricted or PII data.
4. Revoke access for departed team members within the stated operational SLA.
5. Review privileged access periodically and after incidents.

## Classification Levels

| Level | Examples | Default Control |
|---|---|---|
| Public | reference data, public docs | broad read |
| Internal | operational metrics | team read |
| Confidential | financial, strategic, customer business data | group-scoped read |
| PII / Restricted | personal identifiers, health, payment, sensitive attributes | approval, masking, audit |

## PII Controls

- mask or tokenize PII in non-production environments
- keep right-to-erasure procedure documented
- define retention and TTL by dataset
- log access to restricted assets
- document lawful basis or business purpose where compliance requires it

## Audit Sources

| Platform | Source |
|---|---|
| Databricks | Unity Catalog grants, `system.access.audit`, lineage/system tables |
| Fabric | workspace roles, item permissions, OneLake/Fabric lineage and audit surfaces |
| Cross-platform | handoff docs, data contracts, lineage artifacts, deployment logs |

## Review Checklist

- [ ] Data classification exists.
- [ ] Access is group-based.
- [ ] Restricted data has owner approval.
- [ ] Audit query or report exists for access changes.
- [ ] Lineage reaches the source system for Gold/reporting tables.
- [ ] Retention/right-to-erasure is documented where PII exists.

## Source Notes

- Enriched from `data-agents/kb/governance/`
