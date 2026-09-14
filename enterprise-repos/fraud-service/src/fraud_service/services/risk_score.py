class FraudDecision:
    def decide(self, amount, customer_segment):
        score = min(99, amount // 100 + (25 if customer_segment == 'new' else 0))
        return {'score': score, 'decision': 'block' if score >= 80 else 'review' if score >= 50 else 'allow'}
