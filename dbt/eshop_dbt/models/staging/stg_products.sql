select
    product_id,
    name as product_name,
    category,
    price
from {{ source('silver', 'products') }}
