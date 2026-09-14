SERVICE_NAME = "identity-core"
DEPENDS_ON = ['customer-profile', 'notification-core']
PUBLISHES = ['UserCreated', 'IdentityVerified']
SUBSCRIBES = []
