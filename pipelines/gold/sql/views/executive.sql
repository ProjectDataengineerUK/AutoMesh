CREATE OR REPLACE VIEW ${catalog}.${schema}.v_executive AS
SELECT m.event_date, m.source_class, m.total_value, l.lost_value,
       f.consumption, m.source_watermark
FROM ${catalog}.${schema}.gold_market_insights m
LEFT JOIN ${catalog}.${schema}.gold_lost_sales l USING (event_date)
LEFT JOIN ${catalog}.${schema}.gold_finops_costs f
  ON f.usage_date = m.event_date;
