# Retrieval Augmented Generation Operating Pattern

## Purpose

Provide an initial operating pattern for retrieval-augmented generation in AgentCodex-aligned systems.

## When To Use

- Use when model output must be grounded in retrievable enterprise or project knowledge.
- Use when freshness, provenance, or domain specificity matter more than raw model recall.

## When Not To Use

- Do not use when the task is fully solved by deterministic rules or direct database queries.
- Do not use when retrieval quality cannot be monitored or ownership is unclear.

## Core Concepts

- concept: retrieval pipeline includes ingestion, chunking, indexing, retrieval, and answer synthesis
- concept: source quality and metadata quality affect output quality as much as model choice
- concept: provenance must remain visible to users or operators

## Architecture Patterns

- pattern: domain KB plus vector or search index plus answer layer with explicit references
- pattern: hybrid retrieval when lexical recall and semantic recall both matter
- pattern: offline indexing with observable freshness and explicit reindex triggers

## Agent Implications

- relevant roles: `genai-architect`, `llm-specialist`, `ai-data-engineer`, `context-optimizer`
- routing impact: RAG work should pull both local KB and platform/integration pages before implementation
- escalation impact: escalate when retrieval depends on production data access or unapproved indexes

## MCP Implications

- MCP usage: use MCP for current docs or external metadata, not as a substitute for retrieval design
- docs lookup need: vendor-specific search or vector behavior may need official confirmation
- protocol/tooling boundary: keep retrieval evidence explicit even if retrieval execution is remote

## Tradeoffs

- benefit: grounded answers and better domain relevance
- cost: ingestion, metadata, evaluation, and index maintenance
- risk: poor chunking or stale indexes create confident but misleading outputs

## References

- local: `INDEX.md`
- upstream: `.agentcodex/imports/`
- external: `run-llama/llama_index`, `Unstructured-IO/unstructured`, `qdrant/qdrant`

## Local Notes

- repo-specific note: prefer file-based source inventory and explicit domain scope before building a RAG stack
- placeholder: expand later with chunking, evaluation, and vector-store selection guidance
