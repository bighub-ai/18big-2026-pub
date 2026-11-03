select
    order_id,
    customer_id,
    order_ts,
    status
from {{ source('silver', 'orders') }}
