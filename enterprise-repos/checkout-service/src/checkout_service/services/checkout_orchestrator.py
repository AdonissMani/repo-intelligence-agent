IDENTITY_SERVICE = 'identity-core'
CUSTOMER_SERVICE = 'customer-profile'
PAYMENT_SERVICE = 'payment-core'
FRAUD_SERVICE = 'fraud-service'
class CheckoutOrchestrator:
    def submit(self, cart):
        return {'step': 'authorize payment through payment-core', 'owns_decision': False}
