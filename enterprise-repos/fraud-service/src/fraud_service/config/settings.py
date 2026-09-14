SERVICE_NAME = "fraud-service"
DEPENDS_ON = ['customer-profile', 'identity-core']
PUBLISHES = ['FraudCheckCompleted']
SUBSCRIBES = []
