from django.db import models

class AITrainingLog(models.Model):
    ticket_text = models.TextField()
    predicted_label = models.CharField(max_length=100)
    
    # 0 = Bug, 1 = Billing, 2 = Praise, 99 = Question Deflected
    predicted_id = models.IntegerField()
    
    # Model confidence score (0.0 - 100.0)
    confidence = models.FloatField(default=0.0)
    
    # Has a human developer verified this label?
    is_verified = models.BooleanField(default=False)
    
    # If a human corrected the AI, what was the right label?
    corrected_label = models.CharField(max_length=100, blank=True, null=True)
    
    # Optional explanation for the correction (audit trail)
    correction_reason = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    @property
    def final_label(self):
        """Returns the corrected label if available, otherwise the predicted label."""
        return self.corrected_label if self.corrected_label else self.predicted_label

    @property
    def was_corrected(self):
        """True if a human overrode the AI prediction."""
        return bool(self.corrected_label)

    def __str__(self):
        return f"[{self.predicted_label}] {self.ticket_text[:50]}..."

