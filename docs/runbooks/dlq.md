# DLQ recovery

Trigger: contract rejection or poison message. Preserve the original record, correlation ID, source, reason code, and detection timestamp. Confirm valid records continued, correct the producer or contract, then replay through the idempotent ingestion path. Never edit DLQ payloads in place.
