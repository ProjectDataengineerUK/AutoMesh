# Platform Lineage Baseline Lineage Pattern

## Purpose

Describe the minimum lineage expectation for data assets so producers, transformations, and downstream consumers remain traceable.

## When To Use

- Use when defining pipelines, contracts, data products, or KB pages that depend on upstream assets.
- Use when a delivery changes transformation boundaries and downstream impact must be explained.

## When Not To Use

- Do not use as a substitute for detailed platform lineage implementation notes.
- Do not use when the artifact is purely exploratory and has no stable input or output boundary yet.

## Core Concepts

- source asset: table, stream, file set, API feed, or vector collection
- downstream asset: curated table, semantic model, feature set, index, or report
- transformation boundary: the code or platform step that changes meaning, shape, or freshness
- evidence of lineage: repository docs, orchestration metadata, catalog metadata, or platform-native lineage graph

## Architecture Patterns

- file-level lineage: describe source and target assets directly in design and contract files
- pipeline-level lineage: capture hops across ingestion, transformation, serving, and observability layers
- platform-level lineage: integrate with catalog or lineage tooling when local files are insufficient

## Agent Implications

- owning roles: `pipeline-architect`, `data-platform-engineer`, `code-architect`
- metadata roles: `kb-architect`, `doc-updater`
- review implications: `reviewer` and `code-reviewer` should challenge missing upstream/downstream impact

## MCP Implications

- external lineage system use: MCP may expose lineage APIs, but local summaries must remain in-repo
- metadata API dependence: note when lineage is inferred from external metadata rather than explicit design files
- tooling constraints: document gaps when a platform cannot emit precise column-level or job-level lineage

## Tradeoffs

- precision: higher precision improves impact analysis but costs more to maintain
- implementation cost: full automated lineage can require platform coupling
- maintenance burden: stale lineage is worse than narrow but explicit lineage

## References

- local metadata: `../INDEX.md`
- lineage tools: `../../operations/observability/observability-baseline.md`
- upstream references: `.agentcodex/imports/`

## Local Notes

- required identifiers: producer asset, transformation step, consumer asset, and owner
- acceptable evidence: file-based specs first; external screenshots or dashboards are supplementary only
- placeholder: add column-level guidance when catalog tooling is selected
