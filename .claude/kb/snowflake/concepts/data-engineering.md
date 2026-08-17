# Snowflake Data Engineering

## Pipeline Pattern Decision

```
Novo pipeline?
  ├── Latência < 1s         → Snowpipe Streaming (sub-segundo)
  ├── Arquivos em stage     → Snowpipe + Dynamic Tables
  ├── CDC / propagação      → Streams + Tasks MERGE
  └── Transformação geral   → Dynamic Tables (preferido)
```

## Dynamic Tables — Padrão Principal

Dynamic Tables são declarativas e auto-gerenciadas. Preferir sobre Tasks/Streams para novos pipelines.

```sql
-- BRONZE: raw (1 minuto de lag)
CREATE OR REPLACE DYNAMIC TABLE bronze.raw_orders
  TARGET_LAG = '1 minute'
  WAREHOUSE = load_wh_s
AS
SELECT
  $1:order_id::STRING          AS order_id,
  $1:customer_id::STRING       AS customer_id,
  $1:total_amount::NUMBER(10,2) AS total_amount,
  $1:created_at::TIMESTAMP_NTZ  AS source_created_at,
  METADATA$FILENAME             AS source_file,
  CURRENT_TIMESTAMP()           AS loaded_at
FROM @landing.public.orders_stage/;

-- SILVER: limpa e deduplica (5 minutos)
CREATE OR REPLACE DYNAMIC TABLE silver.orders
  TARGET_LAG = '5 minutes'
  WAREHOUSE = transform_wh_m
AS
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY loaded_at DESC) AS rn
  FROM bronze.raw_orders
  WHERE order_id IS NOT NULL AND total_amount > 0
) WHERE rn = 1;

-- GOLD: agregação de negócio (1 hora)
CREATE OR REPLACE DYNAMIC TABLE gold.daily_orders
  TARGET_LAG = '1 hour'
  WAREHOUSE = analytics_wh_xs
AS
SELECT
  DATE_TRUNC('day', source_created_at) AS order_date,
  COUNT(DISTINCT order_id)             AS order_count,
  SUM(total_amount)                    AS total_revenue
FROM silver.orders
GROUP BY 1;
```

## Streams + Tasks — CDC Pattern

```sql
-- Stream captura INSERT/UPDATE/DELETE
CREATE OR REPLACE STREAM silver.orders_changes
  ON TABLE silver.orders
  APPEND_ONLY = FALSE;

-- Task aplica o delta
CREATE OR REPLACE TASK process_order_changes
  WAREHOUSE = transform_wh_m
  SCHEDULE = '5 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('silver.orders_changes')
AS
MERGE INTO gold.customer_lifetime_value AS target
USING (
  SELECT customer_id,
    SUM(CASE WHEN METADATA$ACTION = 'INSERT' THEN total_amount ELSE -total_amount END) AS delta
  FROM silver.orders_changes GROUP BY customer_id
) AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET ltv = ltv + source.delta
WHEN NOT MATCHED THEN INSERT (customer_id, ltv) VALUES (source.customer_id, source.delta);

ALTER TASK process_order_changes RESUME;
```

## Snowpipe (Batch File Ingestion)

```sql
-- Auto-ingest via S3/GCS/ADLS notifications
CREATE OR REPLACE PIPE landing.public.orders_pipe
  AUTO_INGEST = TRUE
AS
COPY INTO raw.orders
FROM @landing.public.orders_stage/
FILE_FORMAT = (TYPE = 'JSON');

-- Monitorar status
SELECT * FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('day', -1, CURRENT_DATE),
  PIPE_NAME => 'landing.public.orders_pipe'
));
```

## Snowpipe Streaming (Sub-segundo)

```python
from snowflake.ingest import SnowflakeStreamingIngestClient

client = SnowflakeStreamingIngestClient(
    account="MY_ACCOUNT", user="SNOWPIPE_USER",
    private_key=private_key, database="RAW", schema="STREAMS"
)
channel = client.open_channel(
    name="ORDERS_STREAM", database="RAW",
    schema="STREAMS", table="ORDERS_STREAM_TABLE"
)
channel.insert_rows(
    [{"order_id": "ORD001", "total": 150.00}],
    offset_token="batch_001"
)
```

## Iceberg Tables (Multi-engine / Open Format)

```sql
CREATE OR REPLACE ICEBERG TABLE gold.orders_iceberg
  EXTERNAL_VOLUME = my_s3_volume
  CATALOG = SNOWFLAKE
  BASE_LOCATION = 'gold/orders/'
AS SELECT * FROM silver.orders;

-- Partition evolution sem full rewrite
ALTER ICEBERG TABLE gold.orders_iceberg
  ADD PARTITION FIELD MONTH(source_created_at);
```

**Usar Iceberg quando:** multi-engine (Spark/Flink/Athena), evitar vendor lock-in, ou dados > 10 TB.

## Monitoramento

```sql
-- Status de Dynamic Tables
SHOW DYNAMIC TABLES IN SCHEMA gold;
SELECT name, target_lag, scheduling_state, last_suspended_reason
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- Task runs (últimas 24h)
SELECT name, state, scheduled_time, error_message
FROM snowflake.account_usage.task_history
WHERE scheduled_time >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP)
ORDER BY scheduled_time DESC;
```

## Guardrails

- Dynamic Tables > Tasks+Streams para novos pipelines (menos código, auto-gerenciadas)
- `TARGET_LAG = '1 second'` em tabelas grandes → usar Snowpipe Streaming
- Streams: consumir completamente antes de COMMIT — não são idempotentes
- Iceberg: verificar suporte de região antes de criar EXTERNAL_VOLUME
- SHOW DYNAMIC TABLES antes de criar — evitar duplicatas silenciosas
