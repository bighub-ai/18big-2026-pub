-- Order fact: one row per order with its total amount and item count.
with orders as (
    select * from {{ ref('stg_orders') }}
),
items as (
    select * from {{ ref('stg_order_items') }}
)

select
    orders.order_id,
    orders.customer_id,
    orders.order_ts,
    orders.status,
    sum(items.line_amount) as order_amount,
    count(*)               as n_items
from orders
join items using (order_id)
group by orders.order_id, orders.customer_id, orders.order_ts, orders.status
