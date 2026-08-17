# DAG Design

Good orchestration keeps task boundaries explicit, retries safe, and operations understandable.

## Design Rules

- each task should do one logical unit of work
- make tasks idempotent against the logical run date or input boundary
- keep transformation logic out of orchestration wrappers when possible
- avoid expensive top-level code in scheduler-parsed modules

## Good Defaults

- `catchup=False` unless backfill is a deliberate requirement
- `max_active_runs=1` when overlapping runs are unsafe
- explicit retry and timeout policy per DAG or task family

## Review Questions

- does rerunning the DAG produce the same intended state?
- are retries safe for every task?
- is the DAG readable without opening five helper modules?
