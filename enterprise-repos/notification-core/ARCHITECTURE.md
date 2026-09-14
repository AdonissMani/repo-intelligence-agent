# Architecture

Domain: notifications.

This repository is part of Atlas Commerce Group's Core Platform area. It exposes capabilities around email, SMS, push notifications, notification templates, delivery tracking.

Dependencies are called through small clients under `src/notification_core/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

Publishes: NotificationSent, NotificationFailed.
Subscribes: PaymentFailed, PaymentRefundRequested, LoanApproved, LoanRejected.
