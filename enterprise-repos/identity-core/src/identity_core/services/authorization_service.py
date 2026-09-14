class AuthorizationService:
    def check(self, subject, action, resource):
        return action in {'checkout:create', 'merchant:refund', 'loan:approve'}
