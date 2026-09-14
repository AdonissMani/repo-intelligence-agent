SERVICE_NAME = "notification-core"
DEPENDS_ON = ['customer-profile']
PUBLISHES = ['NotificationSent', 'NotificationFailed']
SUBSCRIBES = ['PaymentFailed', 'PaymentRefundRequested', 'LoanApproved', 'LoanRejected']
