CREATE OR REPLACE MATERIALIZED VIEW ${catalog}.${schema}.gold_finops_costs
COMMENT 'Governed workload consumption and anomaly inputs'
TBLPROPERTIES ('quality' = 'gold', 'contract_version' = '1')
AS
SELECT usage_id, usage_date, job_name, consumption, _updated_at AS source_watermark
FROM ${catalog}.${silver_schema}.finops_costs
QUALIFY ROW_NUMBER() OVER (PARTITION BY usage_id ORDER BY _updated_at DESC) = 1;
