{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/sales_product_daily.parquet') }}

-- Grain: one row per (day, product). Finer than sales_daily or product_performance on purpose:
-- an interactive dashboard can filter it by time AND category and still re-aggregate to any
-- coarser view (per day, per category, top products). You can't drill below the grain you store.
select
    cast(o.order_ts as date) as day,
    p.product_id,
    p.product_name,
    p.category,
    sum(oi.line_amount)      as revenue,
    sum(oi.qty)              as units
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_orders') }}   o using (order_id)
join {{ ref('stg_products') }} p using (product_id)
group by all
