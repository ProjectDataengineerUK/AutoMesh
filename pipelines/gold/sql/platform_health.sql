CREATE OR REPLACE MATERIALIZED VIEW ${catalog}.${schema}.gold_platform_health
COMMENT 'Validation, observability and recovery health evidence'
TBLPROPERTIES ('quality' = 'gold', 'contract_version' = '1')
AS
SELECT event_id, observed_at, capability_id, result, reason_code
FROM ${catalog}.${evidence_schema}.validation_events
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY observed_at DESC) = 1;
