CREATE OR REPLACE MATERIALIZED VIEW ${catalog}.${schema}.gold_lost_sales
COMMENT 'Governed lost-sales metrics by region and date'
TBLPROPERTIES ('quality' = 'gold', 'contract_version' = '1')
AS
SELECT sale_id, event_date, region, lost_value, _updated_at AS source_watermark
FROM ${catalog}.${silver_schema}.lost_sales
QUALIFY ROW_NUMBER() OVER (PARTITION BY sale_id ORDER BY _updated_at DESC) = 1;
