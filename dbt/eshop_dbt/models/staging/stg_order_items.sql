select
    order_id,
    product_id,
    qty,
    unit_price,
    -- Revenue of a single order line = quantity times unit price.
    -- TODO(6): compute line_amount as qty * unit_price
from {{ source('silver', 'order_items') }}
