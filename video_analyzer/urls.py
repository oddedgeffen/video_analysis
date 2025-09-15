from django.urls import path
from . import views_video, views_chat

urlpatterns = [
    # POST /api/process-video/
    # Upload and start processing a video
    # Request: multipart/form-data with 'video' file
    # Response: { videoId, status, processing_dir, results }
    path('process-video/', views_video.upload_and_process_video, name='process-video'),

    # GET /api/video-status/{video_id}/
    # Check processing status of a video
    # Used by frontend to poll for completion
    # Response: { status, processing_dir?, results?, error? }
    path('video-status/<str:video_id>/', views_video.video_status, name='video-status'),

    # Chat endpoints
    path('chat/start/<str:video_id>/', views_chat.start_chat, name='start-chat'),
    path('chat/question/<int:conversation_id>/', views_chat.ask_question, name='ask-question'),
    path('chat/conversation/<int:conversation_id>/', views_chat.get_conversation, name='get-conversation'),
]