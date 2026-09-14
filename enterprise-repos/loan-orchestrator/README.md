# loan-orchestrator

    loan-orchestrator is owned by Loan Orchestration in Lending Business. It provides loan application workflow, customer verification, risk evaluation orchestration, loan state transitions.

    Important caveat: Owns workflow state; risk-engine owns eligibility scoring.

    ## Runtime Dependencies
    - identity-core
- customer-profile
- risk-engine
- notification-core

    ## Public APIs
    - `POST /v1/loans/apply`
- `GET /v1/loans/{id}`
- `POST /v1/loans/{id}/approve`
