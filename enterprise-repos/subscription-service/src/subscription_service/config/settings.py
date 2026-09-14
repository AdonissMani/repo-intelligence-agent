SERVICE_NAME = "subscription-service"
DEPENDS_ON = ['payment-core', 'customer-profile', 'notification-core']
PUBLISHES = ['SubscriptionSuspended', 'SubscriptionRenewed']
SUBSCRIBES = ['PaymentFailed']
