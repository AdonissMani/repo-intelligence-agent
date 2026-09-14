# Architecture

Domain: ledger and accounting.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around accounting entries, payment ledger, refund reversals, reconciliation primitives.

Dependencies are called through small clients under `src/ledger_core/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: LedgerEntryPosted, LedgerReversalPosted.
Subscribes: PaymentAuthorized, PaymentCaptured, PaymentRefundRequested.
