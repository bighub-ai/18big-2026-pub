{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/product_performance.parquet') }}

select
    p.product_id,
    p.product_name,
    p.category,
    sum(oi.line_amount) as revenue,
    sum(oi.qty)         as units,
    -- Harder: each product's share of total revenue, using a window over the whole result.
    -- TODO(7): revenue_share_pct = 100 * product revenue / total revenue (window sum)
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_products') }} p using (product_id)
group by 1, 2, 3
order by revenue desc
