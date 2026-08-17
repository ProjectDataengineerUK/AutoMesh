# Task Dependencies

Dependencies should express data and control flow clearly, not serve as hidden communication channels.

## Dependency Guidance

- use explicit upstream and downstream relationships
- pass references and lightweight metadata, not large payloads
- use special trigger rules only when the failure semantics are intentional
- treat asset-aware or event-aware scheduling as part of the contract

## Good Defaults

- standard success-based sequencing for normal paths
- `all_done` only for cleanup or reporting paths
- fan-out and fan-in patterns only when runtime variability demands them

## Review Questions

- what data actually flows between tasks?
- does failure of one branch block the right downstream work?
- are retries and trigger rules aligned with business expectations?
