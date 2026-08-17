# External API timeout or rate limit

For timeouts, use bounded retries with backoff and preserve checkpoint state. For HTTP 429, honor `Retry-After` up to the configured ceiling. Confirm idempotency before replay and emit the bounded reason code `TIMEOUT` or `RATE_LIMITED`.
