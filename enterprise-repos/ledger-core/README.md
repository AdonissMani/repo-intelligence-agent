# ledger-core

    ledger-core is owned by Finance Platform in Core Platform. It provides accounting entries, payment ledger, refund reversals, reconciliation primitives.

    Important caveat: Uses refund/reversal language but does not decide refund eligibility.

    ## Runtime Dependencies
    - none

    ## Public APIs
    - `POST /v1/ledger/entries`
- `POST /v1/ledger/reversals`
- `GET /v1/ledger/transactions/{id}`
