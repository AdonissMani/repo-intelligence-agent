# Architecture

Domain: recurring commerce.

This repository is part of Atlas Commerce Group's Retail Business area. It exposes capabilities around recurring billing, subscription lifecycle, scheduled charges, failed-payment retries.

Dependencies are called through small clients under `src/subscription_service/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: SubscriptionSuspended, SubscriptionRenewed.
Subscribes: PaymentFailed.
