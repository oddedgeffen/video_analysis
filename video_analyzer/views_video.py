from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import tempfile
import logging
from .video_processor import process_video_file
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@api_view(['POST'])
def upload_and_process_video(request):
    """
    Handle video upload and initiate video processing
    """
    if 'video' not in request.FILES:
        return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

    video_file = request.FILES['video']
    
    # Generate a unique filename
    timestamp = datetime.now().strftime('%Y_%m_%d___%H_%M_%S')
    filename = f'{timestamp}_{video_file.name}'
    
    try:
        # Save the uploaded file
        video_path = default_storage.save(f'uploads/videos/{filename}', ContentFile(video_file.read()))
        full_path = os.path.join(settings.MEDIA_ROOT, video_path)

        # Process the video
        results = process_video_file(full_path)
        
        # Save results
        result_filename = f'results_{timestamp}.json'
        result_path = default_storage.save(
            f'results/videos/{result_filename}',
            ContentFile(json.dumps(results, indent=2))
        )

        # Return the video ID (timestamp) for status checking
        return Response({
            'videoId': timestamp,
            'status': 'completed',
            'results': results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return Response({
            'error': 'Failed to process video',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def video_status(request, video_id):
    """
    Check the status of video processing
    """
    try:
        # Check if results file exists
        result_path = f'results/videos/results_{video_id}.json'
        
        if default_storage.exists(result_path):
            with default_storage.open(result_path) as f:
                results = json.load(f)
            return Response({
                'status': 'completed',
                'results': results
            })
        else:
            return Response({
                'status': 'processing'
            })

    except Exception as e:
        logger.error(f"Error checking video status: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


