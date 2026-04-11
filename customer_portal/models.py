from django.db import models

class AITrainingLog(models.Model):
    ticket_text = models.TextField()
    predicted_label = models.CharField(max_length=100)
    
    # 0 = Bug, 1 = Billing, 2 = Praise
    predicted_id = models.IntegerField()
    
    # Has a human developer verified this label?
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.predicted_label}] {self.ticket_text[:50]}..."

