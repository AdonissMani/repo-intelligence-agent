# subscription-service

    subscription-service is owned by Subscription Commerce in Retail Business. It provides recurring billing, subscription lifecycle, scheduled charges, failed-payment retries.

    Important caveat: Retry behavior here is subscription billing retry, not payment authorization retry.

    ## Runtime Dependencies
    - payment-core
- customer-profile
- notification-core

    ## Public APIs
    - `POST /v1/subscriptions`
- `POST /v1/subscriptions/{id}/retry`
