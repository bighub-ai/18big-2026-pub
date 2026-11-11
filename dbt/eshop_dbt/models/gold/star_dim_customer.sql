{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/star_dim_customer.parquet') }}

-- Customer dimension of the published star. `email` is deliberately NOT exported:
-- a consumer-facing product carries no PII it doesn't need (more on this in Session 8).
select
    customer_id,
    name,
    city,
    order_count,
    revenue,
    revenue_rank
from {{ ref('dim_customer') }}
