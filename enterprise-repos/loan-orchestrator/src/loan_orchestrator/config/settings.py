SERVICE_NAME = "loan-orchestrator"
DEPENDS_ON = ['identity-core', 'customer-profile', 'risk-engine', 'notification-core']
PUBLISHES = ['LoanApproved', 'LoanRejected']
SUBSCRIBES = ['IdentityVerified']
