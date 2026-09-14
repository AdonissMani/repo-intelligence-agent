IDENTITY_SERVICE = 'identity-core'
CUSTOMER_SERVICE = 'customer-profile'
RISK_SERVICE = 'risk-engine'
class LoanWorkflow:
    def decide(self, risk_result):
        return 'approved' if risk_result['eligible'] else 'rejected'
