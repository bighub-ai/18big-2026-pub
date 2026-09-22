select
    customer_id,
    name,
    email,
    city,
    signup_date
from {{ source('silver', 'customers') }}
