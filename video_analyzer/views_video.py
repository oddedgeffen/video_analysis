from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import tempfile
import logging
import mimetypes
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from .video_processor import process_video_file
from .models import ProcessedVideo
import threading
import boto3
from .utils_clean import _delete_processing_folder, _delete_s3_assets_for_video

logger = logging.getLogger(__name__)

def get_video_directory_structure(video_id: str, ext: str = '.webm') -> dict:
    """
    Get standardized paths for video processing.
    - Local dev: Uses MEDIA_ROOT for persistent debugging
    - Production/S3: Uses temp directories for ephemeral processing
    """
    if getattr(settings, 'USE_S3', False):
        # Production: Use temp directories since files live in S3
        base_dir = Path(tempfile.gettempdir()) / 'video_processing' / video_id
    else:
        # Local dev: Use MEDIA_ROOT for easier debugging/inspection
        base_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'videos' / video_id
    
    return {
        'base_dir': base_dir,
        'original_video': base_dir / f'original{ext}',
        'audio_file': base_dir / 'audio.wav',
        'results_file': base_dir / 'results.json'
    }


@api_view(['POST'])
def s3_presign_upload(request):
    """
    Return presigned POST data for direct S3 upload from the browser.
    Body (optional): { content_type: 'video/webm' }
    Response: { url, fields, key, bucket }
    """
    try:
        if not getattr(settings, 'USE_S3', False):
            return Response({'error': 'S3 is not enabled'}, status=status.HTTP_400_BAD_REQUEST)

        region = getattr(settings, 'AWS_S3_REGION_NAME', None)
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        s3_client = boto3.client('s3', region_name=region)

        timestamp = datetime.now().strftime('%Y_%m_%d___%H_%M_%S')
        unique = uuid4().hex
        # Allow client to send original extension; default to .webm
        ext = request.data.get('ext', '.webm')
        if not ext.startswith('.'):
            ext = f'.{ext}'
        # If content_type not provided, infer from extension
        content_type = request.data.get('content_type')
        if not content_type:
            guessed, _ = mimetypes.guess_type(f'file{ext}')
            content_type = guessed or 'application/octet-stream'
        key = f"uploads/videos/{timestamp}_{unique}/original{ext}"

        conditions = [
            {"acl": "private"},
            ["content-length-range", 1, 1_000_000_000],
        ]
        fields = {"acl": "private", "Content-Type": content_type}

        presigned = s3_client.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=3600,
        )

        return Response({
            'url': presigned['url'],
            'fields': presigned['fields'],
            'key': key,
            'bucket': bucket
        })
    except Exception as e:
        logger.error(f"Error generating presigned POST: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def process_video_from_s3(request):
    """
    Start processing a video that was uploaded directly to S3.
    Body: { key: 'uploads/videos/.../original.webm' }
    """
    try:
        if 'key' not in request.data:
            return Response({'error': 'Missing S3 key'}, status=status.HTTP_400_BAD_REQUEST)

        if not getattr(settings, 'USE_S3', False):
            return Response({'error': 'S3 is not enabled'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and increment trial link usage if provided
        trial_code = request.data.get('trial_code')
        if trial_code:
            try:
                from .models import TrialLink
                trial_link = TrialLink.objects.get(code=trial_code)
                if not trial_link.can_use():
                    return Response({
                        'error': 'Trial link expired or video limit reached'
                    }, status=status.HTTP_400_BAD_REQUEST)
                trial_link.increment_usage()
                logger.info(f"Trial link {trial_code} usage incremented to {trial_link.videos_used}/{trial_link.max_videos}")
            except TrialLink.DoesNotExist:
                return Response({
                    'error': 'Invalid trial code'
                }, status=status.HTTP_400_BAD_REQUEST)

        s3_key = request.data['key']
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        timestamp = datetime.now().strftime('%Y_%m_%d___%H_%M_%S')
        video_id = f"{timestamp}_{uuid4().hex}"
        # Use the actual extension from the S3 key
        ext = Path(s3_key).suffix.lower() or '.webm'
        paths = get_video_directory_structure(video_id, ext)
        paths['base_dir'].mkdir(parents=True, exist_ok=True)

        region = getattr(settings, 'AWS_S3_REGION_NAME', None)
        s3_client = boto3.client('s3', region_name=region)
        logger.info(f"Downloading from s3://{bucket}/{s3_key} to {paths['original_video']}")
        with open(paths['original_video'], 'wb') as f:
            s3_client.download_fileobj(bucket, s3_key, f)

        threading.Thread(target=_process_video_async, args=(paths, video_id), daemon=True).start()

        return Response({
            'videoId': video_id,
            'status': 'processing',
            'processing_dir': str(paths['base_dir'])
        })
    except Exception as e:
        logger.error(f"Error starting processing from S3: {e}")
        _delete_processing_folder(paths)
        _delete_s3_assets_for_video(video_id)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

def _process_video_async(paths: dict, video_id: str) -> None:
    """Background processing task that generates results.json when done."""
    try:
        logger.info('Background processing started')
        results = process_video_file(paths, video_id=video_id)

        # Ensure base directory exists
        paths['base_dir'].mkdir(parents=True, exist_ok=True)

        # Write results file locally only (atomically to avoid partial reads)
        tmp_results_path = paths['results_file'].with_suffix('.json.tmp')
        with open(tmp_results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        os.replace(tmp_results_path, paths['results_file'])


        logger.info('Background processing finished successfully')
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        # Write an error status file so the poller can surface failure
        error_payload = {"status": "error", "error": str(e)}
        try:
            tmp_results_path = paths['results_file'].with_suffix('.json.tmp')
            with open(tmp_results_path, 'w', encoding='utf-8') as f:
                json.dump(error_payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_results_path, paths['results_file'])
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
    
    # Validate and increment trial link usage if provided
    trial_code = request.data.get('trial_code')
    if trial_code:
        try:
            from .models import TrialLink
            trial_link = TrialLink.objects.get(code=trial_code)
            if not trial_link.can_use():
                return Response({
                    'error': 'Trial link expired or video limit reached'
                }, status=status.HTTP_400_BAD_REQUEST)
            trial_link.increment_usage()
            logger.info(f"Trial link {trial_code} usage incremented to {trial_link.videos_used}/{trial_link.max_videos}")
        except TrialLink.DoesNotExist:
            return Response({
                'error': 'Invalid trial code'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate a unique filename and detect original extension
    timestamp = datetime.now().strftime('%Y_%m_%d___%H_%M_%S')
    original_ext = Path(video_file.name).suffix.lower() or '.webm'
    filename = f'{timestamp}_{video_file.name}'
    filename_no_ext = Path(filename).stem
    
    try:
        # Get processing paths
        paths = get_video_directory_structure(filename_no_ext, original_ext)
        paths['base_dir'].mkdir(parents=True, exist_ok=True)
        
        storage_key = None  # Track storage key for cleanup
        
        if getattr(settings, 'USE_S3', False):
            # Production: Save to S3, then download for processing
            storage_rel_path = f"uploads/videos/{filename_no_ext}/original{original_ext}"
            storage_key = default_storage.save(storage_rel_path, ContentFile(video_file.read()))
            try:
                file_url = default_storage.url(storage_key)
                paths['file_url'] = file_url
                logger.info(f"Stored uploaded video to S3 at '{storage_key}', url='{file_url}'")
            except Exception:
                logger.info(f"Stored uploaded video to S3 at '{storage_key}'")
            
            # Download from S3 to local processing directory
            logger.info(f"Downloading from S3 for processing: '{storage_key}'")
            with default_storage.open(storage_key, 'rb') as src, open(paths['original_video'], 'wb') as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            logger.info(f"Downloaded to local processing directory: {paths['original_video']}")
        else:
            # Local dev: Save directly to processing directory
            logger.info(f"Saving video directly to local processing directory: {paths['original_video']}")
            with open(paths['original_video'], 'wb') as dst:
                for chunk in video_file.chunks():
                    dst.write(chunk)
            logger.info(f"Saved video locally at {paths['original_video']}")
        
        # Kick off background processing so the request returns immediately
        threading.Thread(target=_process_video_async, args=(paths, filename_no_ext), daemon=True).start()

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
    
    Response States:
    1. not_found (404): Video ID doesn't exist
    2. processing (200): Video is being processed
    3. completed (200): Processing finished successfully
    4. error (500): Processing failed
    """
    try:
        # Get paths for this video
        paths = get_video_directory_structure(video_id)
        
        # Check if results are ready (local file only)
        if paths['results_file'].exists():
            try:
                with open(paths['results_file'], 'r', encoding='utf-8') as f:
                    results = json.load(f)
            except Exception:
                # If file is being written or partially written, treat as still processing
                return Response({
                    'status': 'processing',
                    'base_dir': str(paths['base_dir']),
                    'progress': {
                        'video_uploaded': paths['original_video'].exists(),
                        'audio_extracted': paths['audio_file'].exists(),
                    }
                })

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
                # Directory exists; treat as processing
                status_info = {
                    'status': 'processing',
                    'base_dir': str(paths['base_dir']),
                    'progress': {
                        'video_uploaded': paths['original_video'].exists(),
                        'audio_extracted': paths['audio_file'].exists(),
                    }
                }
                return Response(status_info)
            else:
                return Response({
                    'status': 'not_found',
                    'error': 'Video not found'
                }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error checking video status: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


