from django.db import models
from django.contrib.auth.models import User


class StrategicComparison(models.Model):
    """Refined Pillar 3: Persisted Strategic flow comparisons for operational optimization."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strategy_a = models.TextField()
    strategy_b = models.TextField()
    comparison_result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Strategic Audit by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
