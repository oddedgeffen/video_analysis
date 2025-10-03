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

    # S3 direct upload flow
    path('s3/presign/', views_video.s3_presign_upload, name='s3-presign-upload'),
    path('process-video-from-s3/', views_video.process_video_from_s3, name='process-video-from-s3'),

    # Chat endpoints
    path('chat/start/<str:video_id>/', views_chat.start_chat, name='start-chat'),
    path('chat/question/<int:conversation_id>/', views_chat.ask_question, name='ask-question'),
    path('chat/conversation/<int:conversation_id>/', views_chat.get_conversation, name='get-conversation'),
    
    # Trial link endpoints
    path('trial/check/<str:code>/', views_chat.check_trial_link, name='check_trial_link'),
]