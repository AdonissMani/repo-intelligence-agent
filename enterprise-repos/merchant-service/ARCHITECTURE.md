# Architecture

Domain: merchant operations.

This repository is part of Atlas Commerce Group's Retail Business area. It exposes capabilities around merchant transaction lookup, merchant refund initiation, settlement views.

Dependencies are called through small clients under `src/merchant_service/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: MerchantRefundRequested.
Subscribes: PaymentRefundRequested.
