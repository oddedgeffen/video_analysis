from django.urls import path
from . import views_video

urlpatterns = [
    path('process-video/', views_video.upload_and_process_video, name='process-video'),
    path('video-status/<str:video_id>/', views_video.video_status, name='video-status'),
]