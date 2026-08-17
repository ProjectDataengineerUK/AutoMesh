# Producer Consumer Baseline Data Contract Spec

## Purpose

Define the minimum file-based contract expected between a producer and its downstream consumers.

## When To Use

- Use when a dataset, event stream, feature output, or serving index is consumed by another team or workflow.
- Use when schema, freshness, compatibility, or ownership must survive team changes.

## When Not To Use

- Do not use for purely private scratch outputs with no durability requirement.
- Do not use as a substitute for physical schema files or test implementations.

## Core Concepts

- producer: job, service, pipeline, or team responsible for publishing the asset
- consumer: downstream pipeline, model, dashboard, application, or external integration
- schema boundary: names, types, semantics, keys, and nullability rules
- SLA or SLO: freshness, availability, latency, or quality expectation

## Architecture Patterns

- schema versioning: explicit version and compatibility statement per contract
- compatibility rule: prefer additive change by default; flag breaking changes explicitly
- validation placement: enforce at publish time and verify again at consume time when risk is high

## Agent Implications

- owning role: `data-contracts-engineer`
- enforcement roles: `schema-designer`, `data-quality-analyst`, `code-reviewer`
- escalation roles: `architect`, `data-platform-engineer`

## MCP Implications

- registry or API involvement: remote registries are optional, not authoritative over repo-local contract intent
- protocol dependency: document whether the contract is table-based, event-based, API-based, or index-based
- current-docs requirement: verify external registry semantics before rollout if using one

## Tradeoffs

- strictness vs agility: stronger contracts reduce incidents but slow producer iteration
- producer cost: contract maintenance adds work to every change
- consumer safety: clear guarantees reduce downstream breakage and ambiguity

## References

- local schema: `../INDEX.md`
- upstream contract patterns: `.agentcodex/imports/`
- official specifications: `OAI/OpenAPI-Specification`, `asyncapi/spec`, `protocolbuffers/protobuf`, JSON Schema

## Local Notes

- breaking-change policy: require explicit decision record and migration notes
- validation command: pair contract updates with repository validation and contract-specific checks
- placeholder: add canonical YAML/JSON schema shape when the contract format is finalized
