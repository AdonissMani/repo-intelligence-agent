# repayment-service

    repayment-service is owned by Repayment in Lending Business. It provides repayment schedules, payment collection, failed repayment handling, ledger integration.

    Important caveat: Overlaps with payment failure terms but owns repayment handling only.

    ## Runtime Dependencies
    - payment-core
- ledger-core
- customer-profile
- notification-core

    ## Public APIs
    - `POST /v1/repayments/collect`
- `GET /v1/repayments/{id}/schedule`
