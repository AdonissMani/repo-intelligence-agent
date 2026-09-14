MAX_RETRIES = 3
GRACE_PERIOD_DAYS = 7
class BillingRetryPolicy:
    def next_action(self, failures):
        return 'suspend' if failures >= MAX_RETRIES else 'retry'
