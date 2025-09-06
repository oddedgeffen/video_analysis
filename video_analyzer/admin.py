from django.contrib import admin
from .models import ProcessedVideo, VideoAnalysisResult

@admin.register(ProcessedVideo)
class ProcessedVideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'duration', 'fps', 'resolution', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'duration', 'frame_count', 'fps', 'resolution')
    search_fields = ('id', 'status')
    ordering = ('-created_at',)

@admin.register(VideoAnalysisResult)
class VideoAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'event_type', 'timestamp', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('event_type', 'video__id')
    readonly_fields = ('created_at',)
    ordering = ('video', 'timestamp')