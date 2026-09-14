PAYMENT_SERVICE = 'payment-core'
LEDGER_SERVICE = 'ledger-core'
class CollectionService:
    def collect(self, installment):
        return {'delegates_payment_to': PAYMENT_SERVICE, 'records_to': LEDGER_SERVICE}
