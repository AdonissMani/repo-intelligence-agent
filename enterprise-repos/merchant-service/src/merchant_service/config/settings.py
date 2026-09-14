SERVICE_NAME = "merchant-service"
DEPENDS_ON = ['payment-core', 'ledger-core', 'identity-core']
PUBLISHES = ['MerchantRefundRequested']
SUBSCRIBES = ['PaymentRefundRequested']
