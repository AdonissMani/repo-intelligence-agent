# Architecture

Domain: payments.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around payment authorization, capture, refund initiation, payment status, payment state transitions.

Dependencies are called through small clients under `src/payment_core/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: PaymentAuthorized, PaymentCaptured, PaymentRefundRequested, PaymentFailed.
Subscribes: none.
