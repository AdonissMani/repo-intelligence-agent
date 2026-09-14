# Architecture

Domain: fraud risk.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around fraud scoring, transaction risk checks, fraud decisions.

Dependencies are called through small clients under `src/fraud_service/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: FraudCheckCompleted.
Subscribes: none.
