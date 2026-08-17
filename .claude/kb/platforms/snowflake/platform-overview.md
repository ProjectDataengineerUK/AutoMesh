# Snowflake Platform Overview

## Purpose

Describe Snowflake as a platform option for governed storage, SQL transformation, data sharing, and controlled serving.

## When To Use

- Use when warehouse-centric analytics and governed data serving are the primary platform need.
- Use when secure sharing, RBAC, and SQL-first transformation align with the operating model.

## When Not To Use

- Do not use when heavy Spark-native processing is the dominant workload.
- Do not use when the team needs a platform-neutral abstraction but only has Snowflake-specific assets in mind.

## Core Concepts

- service model: accounts, warehouses, databases, schemas, and governed objects
- identity model: roles, users, service identities, and object-level privileges
- data model: tables, views, stages, streams, tasks, and data-sharing constructs

## Architecture Patterns

- landing pattern: staged ingestion, curated transforms, and served marts with explicit compute boundaries
- control pattern: role hierarchy, object grants, masking policies, and environment separation
- deployment pattern: SQL plus dbt plus infrastructure artifacts under version control

## Agent Implications

- primary roles: `dbt-specialist`, `schema-designer`, `data-platform-engineer`
- supporting roles: `security-reviewer`, `sql-optimizer`, `data-contracts-engineer`
- escalation path: escalate when account-level policy or sharing model is centrally managed

## MCP Implications

- current-docs need: verify server capabilities and governance features against current platform support
- server/tool alignment: clearly separate metadata access, execution access, and admin access
- external capability constraints: account and role design can block otherwise valid implementation choices

## Tradeoffs

- lock-in: strong warehouse experience with Snowflake-specific semantics
- cost model: easy to start, but warehouse sizing and concurrency need control
- operational complexity: simpler than self-managed systems, but governance still matters
- governance fit: strong for role-based control and shared data products

## References

- local KB: `INDEX.md`
- upstream imports: `.agentcodex/imports/`
- official docs: `Snowflake-Labs/mcp`, `dbt-labs/dbt-core`

## Local Notes

- project conventions: prefer versioned SQL and dbt artifacts over console-only changes
- approved defaults: separate warehouses by workload class and keep grants explicit
- placeholder: expand with sharing, task orchestration, and contract patterns later
