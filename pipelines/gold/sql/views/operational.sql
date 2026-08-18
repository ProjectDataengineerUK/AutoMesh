CREATE OR REPLACE VIEW ${catalog}.${schema}.v_operational AS
SELECT observed_at, capability_id, result, reason_code,
       CASE WHEN observed_at < CURRENT_TIMESTAMP() - INTERVAL 15 MINUTES
            THEN 'STALE' ELSE 'FRESH' END AS freshness_status
FROM ${catalog}.${schema}.gold_platform_health;
