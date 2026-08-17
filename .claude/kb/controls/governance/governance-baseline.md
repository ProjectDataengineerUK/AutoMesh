# Governance Baseline Control Pattern

## Purpose

Provide an initial governance baseline for deciding who can introduce, change, and approve data and AI assets in AgentCodex-managed projects.

## When To Use

- Use when a project needs explicit ownership, approval flow, and evidence for schema, pipeline, KB, or model-adjacent changes.
- Use when multiple teams contribute to the same data platform and implicit rules are no longer safe.

## When Not To Use

- Do not use as a replacement for platform-specific security policy.
- Do not use as a long-form enterprise policy document; keep this page operational and file-based.

## Core Concepts

- policy surface: repositories, workflow artifacts, KB pages, contracts, and deployment definitions
- enforcement point: pull request review, validation commands, and platform-native controls
- evidence: versioned files, decision records, validation output, and ownership metadata

## Architecture Patterns

- preventive control: require file-based specs before implementation or rollout
- detective control: validate routing, roles, KB, and contract artifacts during repository checks
- corrective control: record exceptions through decision records and remediate with bounded follow-up tasks

## Agent Implications

- owning roles: `architect`, `data-platform-engineer`, `governance`-adjacent reviewers
- review roles: `code-reviewer`, `security-reviewer`, `doc-updater`
- escalation path: escalate to platform owners when a control depends on cloud-native policy outside the repo

## MCP Implications

- protocol boundaries: governance decisions stay file-based even when execution uses remote services
- policy/tooling integration: MCP can expose evidence or metadata, but should not become the only source of truth
- remote enforcement dependencies: document external approvals explicitly when enforcement lives off-repo

## Tradeoffs

- strictness: improves auditability but slows unstructured experimentation
- usability cost: contributors must maintain artifacts, not only code
- operational burden: governance decays if ownership and review rules are not kept current

## References

- local controls: `../INDEX.md`
- standards: `docs/DECISIONS.md`
- upstream material: `.agentcodex/imports/`

## Local Notes

- approved enforcement location: repository artifacts first, platform policies second
- validation loop: pair this page with `agentcodex validate` and project-specific review procedures
- placeholder: add domain-specific approval matrices when platform ownership is formalized
