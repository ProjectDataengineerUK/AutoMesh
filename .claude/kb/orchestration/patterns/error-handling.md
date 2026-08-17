# Error Handling

Error handling in orchestration should distinguish transient retry, hard failure, and SLA breach.

## Pattern

- configure retries with bounded backoff for transient dependencies
- send structured failure notifications with task, run, and log context
- keep SLA breach handling separate from ordinary task failure alerts
- use cleanup and notification branches deliberately instead of in-task side effects

## Good Defaults

- retry external I/O more aggressively than deterministic transform code
- route critical failures to an owned escalation path
- capture enough context for operators to reproduce the issue quickly

## Avoid

- unbounded retries on non-idempotent tasks
- email-only alerting for production-critical flows
- mixing remediation logic directly into every task callable
