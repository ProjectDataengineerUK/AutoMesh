CREATE OR REPLACE MATERIALIZED VIEW ${catalog}.${schema}.gold_market_insights
COMMENT 'Governed daily market and insight KPIs'
TBLPROPERTIES ('quality' = 'gold', 'contract_version' = '1')
AS
SELECT event_date, source_class, SUM(metric_value) AS total_value,
       COUNT(*) AS metric_count, MAX(_updated_at) AS source_watermark
FROM ${catalog}.${silver_schema}.market_insights
GROUP BY event_date, source_class;
