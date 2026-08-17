# Azure Platform Overview

## Purpose

Describe Azure as a platform option for data, AI, identity, and control-plane integration in AgentCodex projects.

## When To Use

- Use when the target environment is Azure-native or identity, networking, and compliance requirements are already anchored there.
- Use when Microsoft-managed services are preferred for search, storage, orchestration, or AI-adjacent workloads.

## When Not To Use

- Do not use when the organization is standardized elsewhere and Azure adds unnecessary operational split.
- Do not use when the only requirement is generic compute that can stay platform-agnostic.

## Core Concepts

- service model: managed cloud services with subscription, resource group, and service boundaries
- identity model: Entra ID, managed identities, service principals, and RBAC
- data model: storage accounts, databases, eventing services, and search or analytics services

## Architecture Patterns

- landing pattern: storage plus ingestion plus curated serving layers with explicit identity boundaries
- control pattern: RBAC, private networking, secrets isolation, and policy enforcement
- deployment pattern: infrastructure as code and environment-scoped service configuration

## Agent Implications

- primary roles: `data-platform-engineer`, `architect`, `azure`-focused platform work when added
- supporting roles: `security-reviewer`, `docs-lookup`, `terraform-specialist`
- escalation path: escalate when platform decisions depend on tenant-wide policy or network controls

## MCP Implications

- current-docs need: Azure service capabilities change often enough to verify before implementation
- server/tool alignment: MCP should expose only the minimum service surface needed for the task
- external capability constraints: tenant policy, private endpoints, and identity rules can block assumed flows

## Tradeoffs

- lock-in: strong integration with Microsoft services can reduce portability
- cost model: managed services simplify operations but can hide step-function cost changes
- operational complexity: identity and networking are powerful but require discipline
- governance fit: strong enterprise governance options when centrally managed

## References

- local KB: `INDEX.md`
- upstream imports: `.agentcodex/imports/`
- official docs: `Azure/azure-sdk-for-python`, `Azure-Samples/azure-search-openai-demo`

## Local Notes

- project conventions: keep architecture decisions file-based and avoid portal-only configuration
- approved defaults: managed identity, least privilege, and explicit environment separation
- placeholder: expand with Azure data platform patterns once source inventory is wired into KB pages
