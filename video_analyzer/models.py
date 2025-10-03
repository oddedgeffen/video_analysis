from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import JSONField
import uuid

class ChatConversation(models.Model):
    video = models.ForeignKey('ProcessedVideo', on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_initial_analysis = models.BooleanField(default=False)
    questions_remaining = models.IntegerField(default=settings.MAX_QUESTIONS_PER_VIDEO)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat for Video {self.video.id}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} message in conversation {self.conversation.id}"

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


class VideoConversation(models.Model):
    video_id = models.CharField(max_length=100)
    system_prompt = models.TextField()
    message_history = JSONField(default=list)
    initial_analysis_done = models.BooleanField(default=False)
    trial_link = models.ForeignKey('TrialLink', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_question_count(self):
        user_messages = [msg for msg in self.message_history if msg.get("role") == "user"]
        return len(user_messages) - 1 if len(user_messages) > 0 else 0


class TrialLink(models.Model):
    code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    max_videos = models.IntegerField(default=5)
    videos_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def can_use(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at is not None and timezone.now() >= self.expires_at:
            return False
        return self.videos_used < self.max_videos

    def use_video_slot(self) -> bool:
        if not self.can_use():
            return False
        self.videos_used = self.videos_used + 1
        self.save(update_fields=["videos_used"]) 
        return True