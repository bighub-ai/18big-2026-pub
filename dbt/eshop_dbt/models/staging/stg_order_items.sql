select
    order_id,
    product_id,
    qty,
    unit_price,
    -- Revenue of a single order line = quantity times unit price.
    qty * unit_price as line_amount
from {{ source('silver', 'order_items') }}
