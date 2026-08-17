# Snowpark

## Overview

Snowpark permite executar código Python/Java/Scala dentro do Snowflake compute — zero egress.

**Quando usar:** transformações complexas, Snowpark ML, UDFs vetorizadas.

## Snowpark DataFrames (Python)

```python
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sum as sf_sum, when, lit
from snowflake.snowpark.types import StringType, DecimalType

session = Session.builder.configs({
    "account": "MY_ACCOUNT",
    "user": "MY_USER",
    "private_key_file": "/path/key.p8",
    "database": "ANALYTICS",
    "schema": "GOLD",
    "warehouse": "TRANSFORM_WH"
}).create()

# Leitura e transformação — tudo executado dentro do Snowflake
df = (session.table("analytics.gold.fact_sales")
      .filter(col("sale_date") >= "2026-01-01")
      .with_column("revenue_brl", col("revenue") * lit(5.0))
      .group_by("region", "channel")
      .agg(sf_sum("revenue_brl").alias("total_revenue"))
      .sort(col("total_revenue").desc()))

df.show()
df.write.save_as_table("analytics.gold.revenue_summary", mode="overwrite")
```

## UDFs Vetorizadas (Pandas on Snowflake)

```python
from snowflake.snowpark.functions import pandas_udf
import pandas as pd

@pandas_udf(return_type=DecimalType(10, 2), input_types=[DecimalType(10, 2)])
def apply_discount(prices: pd.Series) -> pd.Series:
    return prices * 0.9

session.sql("SELECT apply_discount(price) FROM gold.products").show()
```

## Snowpark ML

```python
from snowflake.ml.modeling.preprocessing import StandardScaler
from snowflake.ml.modeling.linear_model import LinearRegression
from snowflake.ml.registry import Registry

df = session.table("analytics.ml.customer_features")

scaler = StandardScaler(
    input_cols=["age", "ltv", "order_count"],
    output_cols=["age_scaled", "ltv_scaled", "orders_scaled"]
)
df_scaled = scaler.fit(df).transform(df)

model = LinearRegression(
    input_cols=["age_scaled", "ltv_scaled", "orders_scaled"],
    label_cols=["churn_label"],
    output_cols=["churn_prediction"]
)
model.fit(df_scaled)

registry = Registry(session, database="ANALYTICS", schema="ML")
registry.log_model(model, model_name="churn_predictor", version_name="v1")
```

## Stored Procedures

```python
# Definir como stored proc — executa no Snowflake, chamável via SQL
@session.sproc(name="refresh_gold_layer", replace=True,
               packages=["snowflake-snowpark-python"])
def refresh_gold_layer(session: Session, start_date: str) -> str:
    df = session.table("silver.orders").filter(col("order_date") >= start_date)
    df.write.save_as_table("gold.orders_daily", mode="append")
    return f"Refreshed from {start_date}"

# Chamar via SQL
session.sql("CALL refresh_gold_layer('2026-01-01')").collect()
```

## Guardrails

- **NUNCA** `.collect()` em DataFrames grandes — sempre usar `.write` ou `.show(n)`
- Snowpark ML executa dentro do Snowflake — não há egress de dados de treino
- UDFs Pandas (vetorizadas) são 10–100x mais rápidas que UDFs row-by-row
- Stored Procs são idempotentes por design — usar mode="overwrite" ou "merge"
