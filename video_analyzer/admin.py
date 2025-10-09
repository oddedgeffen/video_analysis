from django.contrib import admin
from .models import ProcessedVideo, VideoAnalysisResult, TrialLink

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

@admin.register(TrialLink)
class TrialLinkAdmin(admin.ModelAdmin):
    list_display = ('code', 'max_videos', 'videos_used', 'videos_remaining', 'expires_at', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('code',)
    readonly_fields = ('code', 'created_at', 'videos_remaining')
    ordering = ('-created_at',)
    actions = ['delete_selected', 'deactivate_selected', 'activate_selected']
    
    def videos_remaining(self, obj):
        return max(0, obj.max_videos - obj.videos_used)
    videos_remaining.short_description = 'Videos Remaining'
    
    def deactivate_selected(self, request, queryset):
        """Deactivate selected trial links"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} trial link(s) were successfully deactivated.')
    deactivate_selected.short_description = "Deactivate selected trial links"
    
    def activate_selected(self, request, queryset):
        """Activate selected trial links"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} trial link(s) were successfully activated.')
    activate_selected.short_description = "Activate selected trial links"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'max_videos', 'videos_used', 'videos_remaining')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )