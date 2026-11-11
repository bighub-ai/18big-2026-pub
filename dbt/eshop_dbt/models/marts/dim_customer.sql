-- Customer dimension: one row per customer enriched with order metrics.
select
    c.customer_id,
    c.name,
    c.email,
    c.city,
    coalesce(ico.order_count, 0) as order_count,
    coalesce(ico.revenue, 0)     as revenue,
    -- Harder: rank customers by revenue (highest revenue = rank 1) using a window function.
    rank() over (order by coalesce(ico.revenue, 0) desc) as revenue_rank
from {{ ref('stg_customers') }} c
left join {{ ref('int_customer_orders') }} ico using (customer_id)
