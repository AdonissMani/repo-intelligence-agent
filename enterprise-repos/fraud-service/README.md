# fraud-service

    fraud-service is owned by Payments Platform in Core Platform. It provides fraud scoring, transaction risk checks, fraud decisions.

    Important caveat: Checkout sometimes calls this directly for pre-screening, which is intentionally duplicated.

    ## Runtime Dependencies
    - customer-profile
- identity-core

    ## Public APIs
    - `POST /v1/fraud/check`
