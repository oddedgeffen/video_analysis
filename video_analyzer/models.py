from django.db import models
from django.utils import timezone

class ProcessedVideo(models.Model):
    video_file = models.FileField(upload_to='videos/uploads/')
    result_file = models.FileField(upload_to='videos/results/', null=True, blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Analysis results
    duration = models.FloatField(null=True)
    frame_count = models.IntegerField(null=True)
    fps = models.FloatField(null=True)
    resolution = models.CharField(max_length=50, null=True)

    def __str__(self):
        return f"Video {self.id} - {self.status}"

class VideoAnalysisResult(models.Model):
    video = models.ForeignKey(ProcessedVideo, on_delete=models.CASCADE, related_name='analysis_results')
    timestamp = models.FloatField()  # Timestamp in video where event was detected
    event_type = models.CharField(max_length=50)  # Type of event detected
    event_data = models.JSONField()  # Detailed event data
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis Result for Video {self.video.id} at {self.timestamp}s"