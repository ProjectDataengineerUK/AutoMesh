# Lakeview publication

The executive and operational manifests are portable definitions for Databricks Lakeview. Local tests validate widget names, source views and metric references without contacting Databricks.

External publication requires `--external`, `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_SQL_WAREHOUSE_ID` and a named allowlisted test target. Missing configuration produces `SKIP_WITH_REASON:MISSING_CREDENTIAL`; no resource is created automatically.
