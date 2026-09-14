# Architecture

Domain: checkout orchestration.

This repository is part of Atlas Commerce Group's Retail Business area. It exposes capabilities around shopping cart checkout, order creation, payment orchestration, promotion validation.

Dependencies are called through small clients under `src/checkout_service/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: CheckoutCompleted, CheckoutFailed.
Subscribes: none.
