from django.urls import path
from . import views_video

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
]