SERVICE_NAME = "payment-core"
DEPENDS_ON = ['fraud-service', 'identity-core', 'ledger-core']
PUBLISHES = ['PaymentAuthorized', 'PaymentCaptured', 'PaymentRefundRequested', 'PaymentFailed']
SUBSCRIBES = []
