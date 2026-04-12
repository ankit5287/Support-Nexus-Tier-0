from django.db import models
from django.contrib.auth.models import User


class ABTestPrediction(models.Model):
    """Pillar 3: Persisted A/B Test Outcome Predictions from Gemini."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strategy_a = models.TextField()
    strategy_b = models.TextField()
    prediction_result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"A/B Prediction by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
