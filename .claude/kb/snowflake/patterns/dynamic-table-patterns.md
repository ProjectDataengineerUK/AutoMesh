# Dynamic Table Patterns

## Medallion Bronze/Silver/Gold

Padrão completo de pipeline declarativo com lag progressivo por camada.

| Camada | TARGET_LAG | Warehouse | Transformações |
|--------|-----------|-----------|----------------|
| Bronze | 1 minuto  | X-Small   | Raw cast, metadata |
| Silver | 5 minutos | Medium    | Dedup, validação, tipos |
| Gold   | 1 hora    | X-Small   | Agregações de negócio |

```sql
-- Bronze → Silver → Gold chain
-- Snowflake propaga automaticamente quando Bronze atualiza
```

## Deduplicação com QUALIFY

```sql
-- Preferir QUALIFY sobre subquery — mais legível e eficiente no Snowflake
CREATE OR REPLACE DYNAMIC TABLE silver.orders
  TARGET_LAG = '5 minutes'
  WAREHOUSE = transform_wh_m
AS
SELECT *
FROM bronze.raw_orders
WHERE order_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY loaded_at DESC) = 1;
```

## SCD Type 2 com Dynamic Tables

```sql
CREATE OR REPLACE DYNAMIC TABLE silver.customers_scd2
  TARGET_LAG = '1 hour'
  WAREHOUSE = transform_wh_m
AS
WITH ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) AS rn,
    LEAD(updated_at) OVER (PARTITION BY customer_id ORDER BY updated_at) AS valid_to
  FROM bronze.customers_changes
)
SELECT
  customer_id,
  name, email, region,
  updated_at        AS valid_from,
  valid_to,         -- NULL = registro atual
  (rn = 1)::BOOLEAN AS is_current
FROM ranked;
```

## FULL REFRESH vs INCREMENTAL

```sql
-- Forçar full refresh (útil após schema change)
ALTER DYNAMIC TABLE silver.orders REFRESH FULL;

-- Verificar modo atual
SHOW DYNAMIC TABLES LIKE 'silver.orders';
-- refresh_mode: INCREMENTAL ou FULL
```

## Pausa e Retomada

```sql
-- Pausar (stop billing sem destruir)
ALTER DYNAMIC TABLE gold.daily_orders SUSPEND;

-- Retomar
ALTER DYNAMIC TABLE gold.daily_orders RESUME;

-- Verificar estado
SELECT name, scheduling_state, last_suspended_reason
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'gold.daily_orders'
));
```

## Quando NÃO usar Dynamic Tables

- Transformações que requerem `MERGE` com lógica de negócio complexa → Streams + Tasks
- Latência < 1 minuto → Snowpipe Streaming + Dynamic Tables com lag baixo
- Precisão transacional (exatamente-uma-vez) → Tasks com stream check
