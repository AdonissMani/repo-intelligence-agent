class ProfileService:
    def get_profile(self, customer_id):
        return {'id': customer_id, 'segment': 'standard', 'verified_income': False}
