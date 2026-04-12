from django.db import models
from django.contrib.auth.models import User

class SupportCase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ticket_text = models.TextField()
    classification = models.CharField(max_length=100)
    
    # 0 = Bug, 1 = Billing, 2 = Praise, 99 = Question Deflected
    category_code = models.IntegerField()
    
    # Reliability score (0.0 - 100.0)
    system_certainty = models.FloatField(default=0.0)
    
    # Has a human specialist reviewed this classification?
    is_reviewed = models.BooleanField(default=False)
    
    # Specialist's overrides
    override_category = models.CharField(max_length=100, blank=True, null=True)
    override_reason = models.CharField(max_length=255, blank=True, null=True)
    
    # Enterprise Workflow Fields
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    TEAM_CHOICES = [
        ('Frontend', 'Frontend'),
        ('Backend', 'Backend'),
        ('Intelligent Triage', 'Intelligent Triage'),
    ]
    PRIORITY_CHOICES = [
        ('P3', 'P3 - Standard'),
        ('P2', 'P2 - Important'),
        ('P1', 'P1 - Critical'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    assigned_team = models.CharField(max_length=25, choices=TEAM_CHOICES, default='Backend')
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='P3')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    @property
    def final_category(self):
        """Returns the specialist's override if available, otherwise the system classification."""
        return self.override_category if self.override_category else self.classification

    @property
    def was_overridden(self):
        """True if a specialist overrode the system's initial classification."""
        return bool(self.override_category)

    def __str__(self):
        return f"[{self.classification}] {self.ticket_text[:50]}..."
