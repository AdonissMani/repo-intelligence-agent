# Architecture

Domain: credit decisioning.

This repository is part of Atlas Commerce Group's Lending Business area. It exposes capabilities around credit scoring, loan eligibility rules, decisioning inputs.

Dependencies are called through small clients under `src/risk_engine/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: RiskDecisionCalculated.
Subscribes: none.
