# Databricks Platform Overview

## Purpose

Describe Databricks as a platform boundary for lakehouse, data engineering, streaming, governance, and AI-adjacent workloads.

## When To Use

- Use when Spark-native processing, medallion pipelines, and lakehouse operations are first-class concerns.
- Use when Unity Catalog, jobs, notebooks, bundles, or platform-managed orchestration are part of the target design.

## When Not To Use

- Do not use when the workload is simple enough for warehouse-only transformation.
- Do not use when the platform requirement is open-format storage without a Databricks control plane.

## Core Concepts

- service model: workspace plus compute plus jobs plus catalog-managed assets
- identity model: workspace access, service principals, tokens, and catalog-level permissions
- data model: tables, volumes, streams, pipelines, and governed assets in the lakehouse

## Architecture Patterns

- landing pattern: ingest to bronze, refine to silver, publish to gold with explicit contract boundaries
- control pattern: Unity Catalog governance, job isolation, and environment-scoped deployment bundles
- deployment pattern: Databricks Asset Bundles or equivalent file-based deployment workflow

## Agent Implications

- primary roles: `lakehouse-architect`, `lakeflow-architect`, `spark-engineer`, `data-platform-engineer`
- supporting roles: `security-reviewer`, `dbt-specialist`, `data-quality-analyst`
- escalation path: escalate when workspace policy, network, or catalog administration is external

## MCP Implications

- current-docs need: confirm product naming and supported deployment path before implementation
- server/tool alignment: remote tooling must map clearly to jobs, pipelines, catalog, or SQL interfaces
- external capability constraints: workspace policy and compute mode can constrain the chosen pattern

## Tradeoffs

- lock-in: strong productivity within Databricks, lower portability of platform-specific assets
- cost model: compute flexibility is powerful but needs guardrails
- operational complexity: central platform features reduce toil but require governance maturity
- governance fit: good fit when catalog, lineage, and platform policy are managed together

## References

- local KB: `INDEX.md`
- upstream imports: `.agentcodex/imports/agentspec/`
- official docs: `databricks/bundle-examples`, `unitycatalog/unitycatalog`

## Local Notes

- project conventions: prefer bundle- and file-based definitions over manual workspace drift
- approved defaults: explicit medallion layer intent, catalog ownership, and deployment environment separation
- placeholder: add bundle, jobs, and Unity Catalog seed pages later
