class LoanEligibilityRules:
    def evaluate(self, profile, requested_amount):
        if not profile.get('verified_income'):
            return {'eligible': False, 'reason': 'income is not verified'}
        if requested_amount > 50000:
            return {'eligible': False, 'reason': 'requested amount exceeds unsecured limit'}
        return {'eligible': True, 'reason': 'within policy'}
