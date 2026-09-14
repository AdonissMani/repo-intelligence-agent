# Architecture

Domain: loan workflows.

This repository is part of Atlas Commerce Group's Lending Business area. It exposes capabilities around loan application workflow, customer verification, risk evaluation orchestration, loan state transitions.

Dependencies are called through small clients under `src/loan_orchestrator/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: LoanApproved, LoanRejected.
Subscribes: IdentityVerified.
