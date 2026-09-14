# merchant-service

    merchant-service is owned by Merchant Operations in Retail Business. It provides merchant transaction lookup, merchant refund initiation, settlement views.

    Important caveat: Many docs say merchant refunds, but it initiates rather than decides eligibility.

    ## Runtime Dependencies
    - payment-core
- ledger-core
- identity-core

    ## Public APIs
    - `POST /v1/merchants/{id}/refunds`
- `GET /v1/merchants/{id}/transactions`
