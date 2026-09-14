class TokenService:
    def issue_token(self, subject, scopes):
        return {'subject': subject, 'scopes': scopes, 'issuer': 'identity-core'}
