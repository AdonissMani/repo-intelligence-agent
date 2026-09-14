SERVICE_NAME = "repayment-service"
DEPENDS_ON = ['payment-core', 'ledger-core', 'customer-profile', 'notification-core']
PUBLISHES = ['RepaymentCollected', 'RepaymentFailed']
SUBSCRIBES = ['PaymentFailed']
