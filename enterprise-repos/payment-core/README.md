# payment-core

    payment-core is owned by Payments Platform in Core Platform. It provides payment authorization, capture, refund initiation, payment status, payment state transitions.

    Important caveat: Refund eligibility lives here; ledger only records the accounting reversal.

    ## Runtime Dependencies
    - fraud-service
- identity-core
- ledger-core

    ## Public APIs
    - `POST /v1/payments/authorize`
- `POST /v1/payments/{id}/capture`
- `POST /v1/payments/{id}/refund`
- `GET /v1/payments/{id}`
