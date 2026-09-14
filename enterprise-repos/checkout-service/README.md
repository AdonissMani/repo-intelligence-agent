# checkout-service

    checkout-service is owned by Checkout in Retail Business. It provides shopping cart checkout, order creation, payment orchestration, promotion validation.

    Important caveat: Orchestrates card acceptance but payment-core owns the final payment decision.

    ## Runtime Dependencies
    - identity-core
- customer-profile
- payment-core
- fraud-service

    ## Public APIs
    - `POST /v1/checkout`
- `POST /v1/checkout/{id}/retry`
