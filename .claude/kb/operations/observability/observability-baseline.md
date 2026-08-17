# Observability Baseline

## Purpose

Define the initial operating view for detecting failures, drift, freshness issues, and performance regressions across data and AI workflows.

## When To Use

- Use when building or reviewing any recurring pipeline, contract validation flow, or retrieval workflow.
- Use when deciding what evidence is required before shipping operational changes.

## When Not To Use

- Do not use as a vendor-specific monitoring manual.
- Do not use when a one-off script has no operational support expectation.

## Core Concepts

- signals: logs, metrics, traces, events, quality checks, and freshness indicators
- failure mode: hard failure, silent failure, degraded output, or runaway cost
- evidence: dashboards, alert definitions, validation reports, and incident records

## Architecture Patterns

- pipeline health pattern: monitor schedule success, latency, freshness, and record counts
- contract health pattern: observe schema drift, null spikes, and compatibility failures
- retrieval health pattern: track indexing delay, query latency, recall proxies, and model-side failures

## Agent Implications

- relevant roles: `pr-test-analyzer`, `silent-failure-hunter`, `build-error-resolver`, `data-quality-analyst`
- routing impact: observability review should trigger before `ship` for stateful or recurring systems
- escalation impact: escalate to platform owners when required telemetry is external to the repo

## MCP Implications

- MCP usage: use MCP to query telemetry systems only when local evidence is insufficient
- docs lookup need: current vendor semantics may require official references before rollout
- protocol/tooling boundary: monitoring state can be remote, but alert intent should still be documented locally

## Tradeoffs

- benefit: faster detection and safer recovery
- cost: instrumentation and alert maintenance add overhead
- risk: excessive alerting hides real incidents; too little alerting hides silent failures

## References

- local: `../INDEX.md`
- upstream: `.agentcodex/imports/`
- external: add official telemetry references when a stack is selected

## Local Notes

- repo-specific note: prefer minimal required signals over exhaustive telemetry at the start
- placeholder: add approved SLI/SLO defaults after `slas-slos` guidance is written
