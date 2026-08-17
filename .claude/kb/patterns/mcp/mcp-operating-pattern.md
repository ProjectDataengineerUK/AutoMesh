# MCP Operating Pattern

## Purpose

Describe how Model Context Protocol should be used as an explicit integration boundary inside AgentCodex workflows.

## When To Use

- Use when an agent needs structured access to remote tools, metadata, docs, or execution surfaces.
- Use when the same remote capability would otherwise be hidden in ad hoc scripts or implicit local state.

## When Not To Use

- Do not use when local files are sufficient and simpler.
- Do not use to bypass repository-local governance, validation, or access-control rules.

## Core Concepts

- concept: MCP is a protocol boundary between local agent reasoning and remote capability exposure
- concept: tool access should be explicit, scoped, and reviewable
- concept: repo-local artifacts remain authoritative over remote conversational state

## Architecture Patterns

- pattern: use MCP for current docs, metadata lookup, or external execution that cannot live locally
- pattern: keep tool selection narrow and aligned to a documented workflow step
- pattern: pair MCP usage with file-based outputs, not transient chat-only conclusions

## Agent Implications

- relevant roles: `docs-lookup`, `context-optimizer`, `domain-researcher`, `architect`
- routing impact: prefer MCP only after local KB and repository evidence are insufficient
- escalation impact: escalate when a server introduces privileged or cross-tenant access

## MCP Implications

- MCP usage: prefer deterministic server choice and minimal tool surface
- docs lookup need: use official or trusted sources when knowledge is time-sensitive
- protocol/tooling boundary: distinguish read-only lookup from state-changing operations

## Tradeoffs

- benefit: consistent access to remote systems and current metadata
- cost: more operational surface and access management
- risk: hidden dependency on external servers if local artifacts are not maintained

## References

- local: `INDEX.md`
- upstream: `.agentcodex/imports/`
- external: `modelcontextprotocol/servers`, `openai/openai-agents-python`

## Local Notes

- repo-specific note: AGENTS.md remains authoritative; MCP augments, not replaces, local instructions
- placeholder: add approved server matrix once `registry/sources.yaml` is wired into the KB
