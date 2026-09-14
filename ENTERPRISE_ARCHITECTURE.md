# Atlas Commerce Group Enterprise Architecture

Atlas Commerce Group has core platform teams for identity, payments, customer data, notifications, and finance. Retail business services compose checkout, merchant operations, and subscription commerce on top of those platforms. Lending business services orchestrate loans, risk decisions, and repayment collection.

The most important payment flow is checkout-service -> fraud-service -> payment-core -> ledger-core. Refunds usually begin in merchant-service, but payment-core decides eligibility and ledger-core records the accounting reversal.

Loan decisions flow through loan-orchestrator -> risk-engine -> customer-profile. Operational questions about timeouts, deployments, or alerts often route to deployment-platform or observability-platform rather than application code.
