{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/sales_daily.parquet') }}

select
    cast(order_ts as date) as day,
    count(*)               as orders,
    sum(order_amount)      as revenue
from {{ ref('fct_orders') }}
group by 1
order by 1
