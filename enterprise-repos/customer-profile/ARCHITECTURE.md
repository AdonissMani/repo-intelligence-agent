# Architecture

Domain: customer data.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around customer profile, preferences, contact details, segmentation metadata.

Dependencies are called through small clients under `src/customer_profile/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: CustomerProfileUpdated.
Subscribes: UserCreated.
