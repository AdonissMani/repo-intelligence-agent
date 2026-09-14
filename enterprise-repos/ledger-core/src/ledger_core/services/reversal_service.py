class ReversalService:
    def create_reversal(self, payment_id, amount):
        return {'payment_id': payment_id, 'amount': amount, 'type': 'refund_reversal'}
