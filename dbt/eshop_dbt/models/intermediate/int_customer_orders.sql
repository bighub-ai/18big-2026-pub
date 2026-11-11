-- One row per customer with their order count and total revenue.
with orders as (
    select * from {{ ref('stg_orders') }}
),
items as (
    select * from {{ ref('stg_order_items') }}
)

select
    orders.customer_id,
    count(distinct orders.order_id) as order_count,
    sum(items.line_amount)          as revenue
from orders
join items using (order_id)
group by orders.customer_id
