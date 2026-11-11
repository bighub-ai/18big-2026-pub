{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/sales_daily.parquet') }}

-- TODO(7): daily revenue and order count from fct_orders (group by calendar day)
