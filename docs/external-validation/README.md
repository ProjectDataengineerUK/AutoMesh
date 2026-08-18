# External validation runbook

The harness is local-first and cloud-optional:

```bash
python -m pipelines.external_validation.cli --mode preflight
python -m pipelines.external_validation.cli --mode dry-run --report artifacts/external-validation.json
```

`publish` is intentionally not wired to a live workspace until an approved Databricks adapter, environment and manual gate are supplied. Missing workspace context is reported as `SKIP_EXTERNAL`; malformed or unsafe configuration is a failure.
