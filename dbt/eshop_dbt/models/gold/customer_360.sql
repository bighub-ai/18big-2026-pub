{{ config(materialized='external', location=env_var('ESHOP_GOLD') ~ '/customer_360.parquet') }}

select
    customer_id,
    name,
    city,
    order_count,
    revenue,
    revenue_rank,
    -- A simple business segmentation for consumers of this data product.
    case when revenue > 0 then 'active' else 'prospect' end as segment
from {{ ref('dim_customer') }}
