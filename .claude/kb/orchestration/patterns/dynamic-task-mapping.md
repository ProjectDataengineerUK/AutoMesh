# Dynamic Task Mapping

Use runtime-generated task fan-out only when workload cardinality is not known before execution.

## Pattern

- produce the runtime collection first
- map one clear unit of work across that collection
- aggregate results explicitly in a fan-in step when needed
- pass shared configuration through a pinned parameter layer, not copy-pasted task logic

## Good Defaults

- keep mapped task payloads lightweight
- cap parallelism according to system and platform limits
- store large artifacts externally and pass references downstream

## Avoid

- dynamic mapping for fixed-size workloads
- huge XCom payloads from mapped tasks
- fan-out without a clear failure and aggregation strategy
