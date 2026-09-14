SERVICE_NAME = "checkout-service"
DEPENDS_ON = ['identity-core', 'customer-profile', 'payment-core', 'fraud-service']
PUBLISHES = ['CheckoutCompleted', 'CheckoutFailed']
SUBSCRIBES = []
