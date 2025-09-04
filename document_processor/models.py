from django.db import models
from django.utils import timezone

class ProcessedDocument(models.Model):
    original_document = models.FileField(upload_to='documents/original/')
    processed_document = models.FileField(upload_to='documents/processed/', null=True, blank=True)
    old_logo = models.ImageField(upload_to='logos/old/')
    new_logo = models.ImageField(upload_to='logos/new/')
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(null=True, blank=True)
    delete_running = models.BooleanField(default=False)

    def __str__(self):
        return f"Document {self.id} - {self.status}"

class Feedback(models.Model):
    rating = models.IntegerField(null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback #{self.id} - Rating: {self.rating if self.rating else 'No rating'}"
