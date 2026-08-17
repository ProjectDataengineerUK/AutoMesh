# Access Control Baseline Control Pattern

## Purpose

Provide an initial access-control model for deciding who can read, write, deploy, and administer data and AI assets.

## When To Use

- Use when onboarding a new platform, integration, or privileged workflow.
- Use when access scope is broader than a single developer machine or local experiment.

## When Not To Use

- Do not use as a replacement for provider IAM documentation.
- Do not use to justify shared admin credentials or undocumented break-glass access.

## Core Concepts

- policy surface: identities, roles, service principals, secrets, and permission scopes
- enforcement point: IAM policy, catalog grants, secrets manager, CI identity, or runtime service identity
- evidence: role assignments, review records, and deploy-time validation

## Architecture Patterns

- preventive control: least-privilege grants and separate read/write/admin scopes
- detective control: permission reviews, access reports, and denied-access auditing
- corrective control: revoke excess permissions and rotate compromised credentials

## Agent Implications

- owning roles: `security-reviewer`, `architect`, `data-platform-engineer`
- review roles: `code-reviewer`, `reviewer`
- escalation path: escalate to cloud or platform administrators for off-repo permissions

## MCP Implications

- protocol boundaries: MCP access should inherit least privilege rather than bypass it
- policy/tooling integration: tool configuration must not hide who is acting and with what scope
- remote enforcement dependencies: document any privileged remote server assumptions explicitly

## Tradeoffs

- strictness: tighter controls reduce blast radius but increase setup friction
- usability cost: short-lived credentials and segmented roles add workflow overhead
- operational burden: access reviews must be maintained or the model drifts

## References

- local controls: `../INDEX.md`
- standards: `../../operations/incidents/INDEX.md`
- upstream material: `.agentcodex/imports/`

## Local Notes

- approved enforcement location: provider IAM and catalog permissions, backed by repo-local documentation
- validation loop: review access assumptions during design and before ship
- placeholder: add service-account patterns once platform choices are stable
