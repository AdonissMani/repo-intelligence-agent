FRAUD_SERVICE = 'fraud-service'
IDENTITY_SERVICE = 'identity-core'
class PaymentAuthorizer:
    def authorize(self, amount, risk_decision):
        if amount <= 0:
            return 'declined'
        return 'authorized' if risk_decision != 'block' else 'declined'
