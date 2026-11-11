{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/customer_360.parquet') }}

select
    customer_id,
    name,
    city,
    order_count,
    revenue,
    revenue_rank,
    -- A simple business segmentation for consumers of this data product.
    -- TODO(7): 'active' when revenue > 0, otherwise 'prospect'
from {{ ref('dim_customer') }}
