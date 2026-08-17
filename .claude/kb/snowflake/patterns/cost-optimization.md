# Snowflake Cost Optimization Patterns

## Warehouse Sizing Guide

| Workload                  | Tamanho    | AUTO_SUSPEND | Observação                        |
|---------------------------|-----------|--------------|-----------------------------------|
| BI / dashboards ad-hoc    | X-Small   | 30s          | Multicluster desabilitado         |
| dbt / transformações      | Medium    | 60s          | Escalar para Large em runs grandes|
| Cortex Analyst / Search   | Small     | 30s          | Cortex tem seu próprio compute    |
| Snowpipe / ingestão       | Small     | 60s          | Auto-resume obrigatório           |
| Carga histórica (1x)      | Large     | 60s          | Desligar manualmente após uso     |
| Snowpark ML training      | Medium–Large | 120s      | Monitorar spill no Query Profile  |

## Top Consumidores (últimos 7 dias)

```sql
SELECT
  warehouse_name, warehouse_size,
  ROUND(SUM(credits_used_cloud_services), 2) AS total_credits,
  ROUND(SUM(credits_used_cloud_services) * 3.0, 2) AS est_cost_usd,
  COUNT(*) AS query_count
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP)
GROUP BY 1, 2
ORDER BY total_credits DESC;
```

## Detecção de Spill (Sinal de Refatoração)

```sql
-- Spill remoto > 1 GB → refatorar imediatamente
SELECT query_id, query_text, warehouse_size,
       ROUND(bytes_spilled_to_remote_storage / 1e9, 2) AS remote_spill_gb,
       ROUND(total_elapsed_time / 1000.0, 1) AS elapsed_s
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP)
  AND bytes_spilled_to_remote_storage > 1e9
ORDER BY bytes_spilled_to_remote_storage DESC LIMIT 10;
```

## Clustering Ineficiente

```sql
-- Queries sem pruning = clustering não sendo usado
SELECT query_id, partitions_scanned, partitions_total,
       ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 1) AS scan_pct
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP)
  AND partitions_total > 100
  AND partitions_scanned = partitions_total
ORDER BY partitions_total DESC LIMIT 10;

-- Verificar profundidade de clustering
SELECT SYSTEM$CLUSTERING_INFORMATION('gold.fact_sales', '(TO_DATE(sale_timestamp), region_code)');
```

## Storage Otimização

```sql
-- Time Travel em staging não precisa de 14 dias
ALTER TABLE raw.staging.temp_events SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Tabelas grandes sem acesso recente
SELECT table_name, ROUND(bytes / 1e9, 2) AS size_gb, last_altered
FROM information_schema.tables
WHERE table_type = 'BASE TABLE' AND bytes > 1e9
ORDER BY bytes DESC;
```

## Resource Monitor

```sql
CREATE OR REPLACE RESOURCE MONITOR monthly_budget
  WITH CREDIT_QUOTA = 500
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 80 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE analytics_wh SET RESOURCE_MONITOR = monthly_budget;
```

## Cortex AI Cost Control

```sql
-- Monitorar créditos Cortex (AI functions)
SELECT DATE_TRUNC('day', start_time) AS day,
       SUM(credits_used_cloud_services) AS cortex_credits
FROM snowflake.account_usage.query_history
WHERE start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP)
  AND (query_text ILIKE '%AI_COMPLETE%' OR query_text ILIKE '%AI_EMBED%')
GROUP BY 1 ORDER BY 1 DESC;
```

**Regras Cortex:**
- Batch > row-by-row: `SELECT AI_COMPLETE(...) FROM table` não `FOR EACH ROW`
- Cache embeddings: `AI_EMBED` não muda se o texto não muda — usar tabela de cache
- Modelo por complexidade: `claude-haiku-4-5` para classificação, `claude-sonnet-4-6` para análise

## Guardrails

- Medir créditos antes e depois de qualquer mudança de sizing
- Downsize → testar com 1 query em horário de baixo movimento
- Resource Monitor SUSPEND → avisar usuários antes de aplicar em produção
- NUNCA aumentar warehouse sem Query Profile justificando a necessidade
