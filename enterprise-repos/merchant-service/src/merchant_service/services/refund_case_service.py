PAYMENT_SERVICE = 'payment-core'
LEDGER_SERVICE = 'ledger-core'
class RefundCaseService:
    def open_case(self, payment_id):
        return {'payment_id': payment_id, 'delegates_eligibility_to': PAYMENT_SERVICE}
