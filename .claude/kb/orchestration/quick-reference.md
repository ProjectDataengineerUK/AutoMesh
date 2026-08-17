# Orchestration Quick Reference

## Core Questions

- What depends on what?
- What retries safely and what does not?
- Where should orchestration stop and transformation logic begin?
- How is failure observed and recovered?

## Good Defaults

- prefer explicit dependency graphs
- keep orchestration thin
- make idempotency visible
- design with operations in mind
