# Architecture

Domain: loan repayment.

This repository is part of Atlas Commerce Group's Lending Business area. It exposes capabilities around repayment schedules, payment collection, failed repayment handling, ledger integration.

Dependencies are called through small clients under `src/repayment_service/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: RepaymentCollected, RepaymentFailed.
Subscribes: PaymentFailed.
