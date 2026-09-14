from payment_core.payments.refunds.eligibility import RefundEligibilityPolicy
PUBLISHES_EVENT = 'PaymentRefundRequested'
class RefundWorkflow:
    def request_refund(self, payment):
        allowed, reason = RefundEligibilityPolicy().decide(payment)
        return {'allowed': allowed, 'reason': reason, 'event': PUBLISHES_EVENT if allowed else None}
