# Validation environments

The inventory command reports only whether required variable names are configured. It never copies, hashes, or logs values.

```bash
python scripts/validation/run_validation.py inventory --environment local
```

External probes require both explicit enablement and complete capability configuration. They use named test resources and never provision infrastructure.
