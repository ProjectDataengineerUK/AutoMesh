# Airflow degraded

Check scheduler, triggerer, and DAG processor health separately. When local resources are constrained, run the isolated Airflow 3.0 DagBag gate. Record `INFRASTRUCTURE_ERROR` without treating a successful isolated import as proof of scheduler health.
