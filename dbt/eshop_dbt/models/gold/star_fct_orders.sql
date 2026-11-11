{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/star_fct_orders.parquet') }}

-- The core star schema, published as a Gold data product for BI tools with a modeling layer
-- (e.g. Power BI wants a star: relate star_fct_orders.customer_id -> star_dim_customer.customer_id).
select
    order_id,
    customer_id,
    order_ts,
    cast(order_ts as date) as order_date,
    status,
    order_amount,
    n_items
from {{ ref('fct_orders') }}
