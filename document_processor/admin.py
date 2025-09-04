from django.contrib import admin
from .models import ProcessedDocument, Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'rating', 'feedback_text', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('feedback_text',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(ProcessedDocument)
class ProcessedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
