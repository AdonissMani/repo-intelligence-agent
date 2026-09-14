LEDGER_SERVICE = 'ledger-core'
class RefundEligibilityPolicy:
    def decide(self, payment):
        if payment.get('state') not in {'captured', 'settled'}:
            return False, 'payment is not captured or settled'
        if payment.get('chargeback_open'):
            return False, 'chargeback already owns the dispute path'
        if payment.get('refunded_amount', 0) >= payment.get('amount', 0):
            return False, 'payment has already been fully refunded'
        return True, 'eligible for merchant or support initiated refund'
