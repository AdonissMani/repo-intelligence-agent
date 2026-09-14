# Architecture

Domain: identity and access.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around authentication, authorization, token issuance, service identity.

Dependencies are called through small clients under `src/identity_core/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: UserCreated, IdentityVerified.
Subscribes: none.
