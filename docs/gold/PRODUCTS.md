# AutoMesh Gold products

The Fase 7 MVP publishes four governed products:

- `gold_market_insights`: market and insight metrics by source class/date.
- `gold_lost_sales`: lost-sales facts by sale, region and date.
- `gold_finops_costs`: workload consumption by job/date.
- `gold_platform_health`: validation and observability evidence by capability/event.

Each product has a declared grain, business key, watermark, owner, required columns and sensitivity metadata in `pipelines/gold/contracts/`. Gold builds are replay-safe and fail closed on null or duplicate keys.
