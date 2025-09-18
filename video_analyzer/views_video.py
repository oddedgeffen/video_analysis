from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import tempfile
import logging
import json
from datetime import datetime
from pathlib import Path
from .video_processor import process_video_file
from .models import ProcessedVideo
import threading

logger = logging.getLogger(__name__)

def get_video_directory_structure(video_id: str) -> dict:
    """
    Get standardized paths for video processing directory structure
    
    Directory Structure:
    media/uploads/videos/{video_id}/
    ├── original.webm      # Original uploaded video
    ├── audio.wav         # Extracted audio
    ├── processed_frames/ # Directory for frame-by-frame analysis
    └── results.json      # Processing results and metadata
    
    Args:
        video_id: Unique identifier for the video (timestamp)
    
    Returns:
        Dictionary containing all relevant paths
    """
    base_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'videos' / video_id
    
    return {
        'base_dir': base_dir,
        'original_video': base_dir / 'original.webm',
        'audio_file': base_dir / 'audio.wav',
        'frames_dir': base_dir / 'processed_frames',
        'results_file': base_dir / 'results.json'
    }


def _process_video_async(paths: dict, timestamp: str) -> None:
    """Background processing task that generates results.json when done."""
    try:
        logger.info('Background processing started')
        results = process_video_file(paths)

        # Ensure base directory exists
        paths['base_dir'].mkdir(parents=True, exist_ok=True)

        # Write canonical results file for polling endpoint
        with open(paths['results_file'], 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Create DB record referencing the results file
        try:
            video = ProcessedVideo.objects.create(
                video_file=str(paths['original_video']),
                result_file=str(paths['results_file']),
                status='completed',
                duration=results.get('video_metadata', {}).get('duration_seconds'),
                frame_count=results.get('video_metadata', {}).get('total_frames'),
                fps=results.get('video_metadata', {}).get('fps'),
                resolution=f"{results.get('video_metadata', {}).get('frame_width')}x{results.get('video_metadata', {}).get('frame_height')}"
            )
            logger.info(f"ProcessedVideo created with id={video.id}")
        except Exception as db_err:
            logger.error(f"Failed to create ProcessedVideo: {db_err}")

        logger.info('Background processing finished successfully')
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        # Write an error status file so the poller can surface failure
        error_payload = {"status": "error", "error": str(e)}
        try:
            with open(paths['results_file'], 'w', encoding='utf-8') as f:
                json.dump(error_payload, f, ensure_ascii=False, indent=2)
        except Exception as write_err:
            logger.error(f"Failed writing error results file: {write_err}")

@api_view(['POST'])
def upload_and_process_video(request):
    """
    Handle video upload and initiate video processing.
    
    Video Flow:
    1. Browser:
        - Video is recorded in browser memory (MediaRecorder API)
        - Stored as Blob in browser RAM
        - Converted to File object for upload
    
    2. Upload Process:
        - Video sent as multipart/form-data in HTTP request
        - Temporarily stored in Django's RAM during upload
        - Django's request.FILES provides file-like object
    
    3. Local Storage (Development):
        a. Initial Save:
            - Video saved to MEDIA_ROOT/uploads/videos/{timestamp}_{filename}
            - Uses default_storage (local FileSystemStorage)
        b. Processing:
            - Video loaded from local storage for processing
            - Audio extracted and saved temporarily
            - Original video remains in place during processing
    
    4. S3 Storage (Production):
        a. Initial Save:
            - Video uploaded directly to S3 (default_storage = S3Boto3Storage)
            - Path: s3://bucket/uploads/videos/{timestamp}_{filename}
        b. Processing:
            - Video downloaded from S3 to local temp directory
            - Processed locally (audio extraction, transcription)
            - Results uploaded back to S3
            - Local temp files cleaned up
    
    Note: The actual storage backend (local vs S3) is determined by
    DEFAULT_FILE_STORAGE setting in Django settings.
    """
    if 'video' not in request.FILES:
        return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)

    video_file = request.FILES['video']
    
    # Generate a unique filename
    timestamp = datetime.now().strftime('%Y_%m_%d___%H_%M_%S')
    filename = f'{timestamp}_{video_file.name}'
    filename_no_ext = Path(filename).stem
    
    try:
        # Create directory structure for this video
        paths = get_video_directory_structure(filename_no_ext)
        paths['base_dir'].mkdir(parents=True, exist_ok=True)
        
        # Save the uploaded file in its dedicated directory
        # In development: Saves to local filesystem
        # In production: Uploads to S3 bucket
        with open(paths['original_video'], 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        logger.info(f"Saved video to {paths['original_video']}")
        
        # Kick off background processing so the request returns immediately
        threading.Thread(target=_process_video_async, args=(paths, timestamp), daemon=True).start()

        # Immediately inform the client to start polling
        return Response({
            'videoId': filename_no_ext,
            'status': 'processing',
            'processing_dir': str(paths['base_dir'])
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
    Check the status of video processing.
    
    Purpose:
    - Frontend polling endpoint to track video processing progress
    - Called repeatedly by frontend after upload until processing completes
    - Provides status updates and final results when ready
    
    Usage Flow:
    1. Frontend uploads video to /process-video/ endpoint
    2. Receives videoId in response
    3. Starts polling this endpoint (/video-status/{videoId}/)
    4. Continues polling until status is 'completed' or 'error'
    5. Displays results or error message to user
    
    Example Frontend Code:
    ```javascript
    // After upload succeeds
    const checkStatus = async (videoId) => {
      const response = await fetch(`/api/video-status/${videoId}/`);
      const data = await response.json();
      
      if (data.status === 'completed') {
        // Show results
        displayResults(data.results);
      } else if (data.status === 'processing') {
        // Check again in 2 seconds
        setTimeout(() => checkStatus(videoId), 2000);
      } else if (data.status === 'error') {
        // Show error
        displayError(data.error);
      }
    };
    ```
    
    Response States:
    1. not_found (404): Video ID doesn't exist
       {
         "status": "not_found",
         "error": "Video processing directory not found"
       }
    
    2. processing (200): Video is being processed
       {
         "status": "processing",
         "processing_dir": "/path/to/processing/dir"
       }
    
    3. completed (200): Processing finished successfully
       {
         "status": "completed",
         "processing_dir": "/path/to/processing/dir",
         "results": { ... processing results ... }
       }
    
    4. error (500): Processing failed
       {
         "status": "error",
         "error": "Error details..."
       }
    """
    try:
        # Get paths for this video
        paths = get_video_directory_structure(video_id)
        
        # Check if results are ready
        if paths['results_file'].exists():
            with open(paths['results_file'], 'r', encoding='utf-8') as f:
                results = json.load(f)

            # If the background job reported an error
            if isinstance(results, dict) and results.get('status') == 'error':
                return Response({
                    'status': 'failed',
                    'error': results.get('error', 'Processing failed')
                })

            # Include file paths in response
            results['file_paths'] = {
                'video': str(paths['original_video']),
                'audio': str(paths['audio_file']),
                'frames': str(paths['frames_dir']),
                'results': str(paths['results_file'])
            }

            return Response({
                'status': 'completed',
                'base_dir': str(paths['base_dir']),
                'results': results
            })
        else:
            # Check processing status
            if paths['base_dir'].exists():
                # Directory exists; treat as processing regardless of file write race
                status_info = {
                    'status': 'processing',
                    'base_dir': str(paths['base_dir']),
                    'progress': {
                        'video_uploaded': paths['original_video'].exists(),
                        'audio_extracted': paths['audio_file'].exists(),
                        'frames_processed': paths['frames_dir'].exists() and any(paths['frames_dir'].iterdir())
                    }
                }
                return Response(status_info)
            else:
                return Response({
                    'status': 'not_found',
                    'error': 'Video not found'
                }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error checking video status: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


