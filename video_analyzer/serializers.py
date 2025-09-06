from rest_framework import serializers
from .models import ProcessedDocument, Feedback

class ProcessedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedDocument
        fields = ['id', 'original_document', 'processed_document', 'old_logo', 'new_logo', 
                 'status', 'created_at', 'updated_at', 'error_message']
        read_only_fields = ['processed_document', 'status', 'error_message']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'rating', 'feedback_text', 'created_at'] 