from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import VideoConversation
from .views_video import get_video_directory_structure
from .services.claude_service import ClaudeVideoAnalysisService
import json
import boto3
import threading
import logging
import shutil

logger = logging.getLogger(__name__)

def _delete_s3_assets_for_video(video_id: str) -> None:
    """
    Delete all S3 objects under the video's folder prefixes after transcript use.
    Handles both legacy "uploads/videos/..." and django-storages "media/uploads/videos/..." prefixes.
    """
    try:
        if not getattr(settings, 'USE_S3', False):
            return
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        region = getattr(settings, 'AWS_S3_REGION_NAME', None)
        s3 = boto3.client('s3', region_name=region)

        prefixes = [
            f"uploads/videos/{video_id}/",
            f"media/uploads/videos/{video_id}/",
        ]

        paginator = s3.get_paginator('list_objects_v2')
        for prefix in prefixes:
            try:
                for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    if 'Contents' not in page:
                        continue
                    objects = [{'Key': obj['Key'] } for obj in page['Contents']]
                    # Delete in chunks of up to 1000
                    for i in range(0, len(objects), 1000):
                        s3.delete_objects(
                            Bucket=bucket,
                            Delete={
                                'Objects': objects[i:i+1000],
                                'Quiet': True
                            }
                        )
                logger.info(f"Deleted S3 assets with prefix '{prefix}' for video_id={video_id}")
            except Exception as inner_e:
                logger.error(f"Failed deleting S3 objects for prefix '{prefix}': {inner_e}")
    except Exception as e:
        logger.error(f"Failed to delete S3 assets for video_id={video_id}: {e}")

def _cleanup_assets_for_video(video_id: str) -> None:
    """
    Remove all artifacts related to a video from both S3 (if enabled) and local storage.
    This is safe to run regardless of storage backend; it will no-op where not applicable.
    """
    try:
        # Delete S3 objects (if enabled)
        if getattr(settings, 'USE_S3', False):
            _delete_s3_assets_for_video(video_id)

        # Delete local processing directory (temp or MEDIA_ROOT path)
        try:
            paths = get_video_directory_structure(video_id)
            base_dir = paths['base_dir']
            if base_dir.exists():
                shutil.rmtree(base_dir, ignore_errors=True)
                logger.info(f"Deleted local processing directory '{base_dir}' for video_id={video_id}")
        except Exception as local_e:
            logger.error(f"Failed deleting local directory for video_id={video_id}: {local_e}")
    except Exception as e:
        logger.error(f"Cleanup failed for video_id={video_id}: {e}")

@api_view(['POST'])
def start_chat(request, video_id):
    """
    Start a new chat conversation for a video.
    If this is the first conversation, it will include an initial analysis.
    """
    try:
        # Locate processed assets
        paths = get_video_directory_structure(video_id)

        # Load the video results
        with open(str(paths['results_file']), 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        service = ClaudeVideoAnalysisService()
        guidelines = settings.INITIAL_SYSTEM_PROMPT
        system_prompt = service.build_system_prompt(transcript_data, guidelines)

        # Get or create the JSON-based conversation per video
        convo, created = VideoConversation.objects.get_or_create(
            video_id=video_id,
            defaults={
                'system_prompt': system_prompt,
                'message_history': []
            }
        )

        # If we created the record or initial analysis not done, run initial analysis once
        if created or not convo.initial_analysis_done:
            init_res = service.get_initial_analysis(system_prompt)
            if not init_res.get('success'):
                return Response({'error': init_res.get('error', 'Failed to generate initial analysis')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Append initial user prompt and assistant analysis to history
            initial_prompt = init_res['initial_prompt']
            assistant_text = init_res['analysis']
            convo.message_history = convo.message_history + [
                {"role": "user", "content": initial_prompt},
                {"role": "assistant", "content": assistant_text}
            ]
            convo.initial_analysis_done = True
            convo.system_prompt = system_prompt
            convo.save()

        # Compute remaining questions based on history
        limit_info = ClaudeVideoAnalysisService().check_question_limit(convo.message_history)
        remaining = limit_info['remaining']

        # After transcript is incorporated into chat, delete S3 and local artifacts asynchronously
        try:
            threading.Thread(target=_cleanup_assets_for_video, args=(video_id,), daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to schedule cleanup for video_id={video_id}: {e}")

        return Response({
            'conversation_id': convo.id,
            'questions_remaining': remaining,
            'messages': convo.message_history
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def ask_question(request, conversation_id):
    """
    Ask a follow-up question in an existing conversation
    """
    try:
        if 'question' not in request.data:
            return Response({
                'error': 'No question provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        convo = get_object_or_404(VideoConversation, id=conversation_id)

        service = ClaudeVideoAnalysisService()
        limit_info = service.check_question_limit(convo.message_history)
        if limit_info['limit_reached']:
            return Response({'error': 'Maximum number of questions reached for this video'}, status=status.HTTP_400_BAD_REQUEST)

        question = request.data['question']
        send_res = service.send_chat_message(convo.system_prompt, convo.message_history, question)
        if not send_res.get('success'):
            return Response({'error': send_res.get('error', 'Failed to get response')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        convo.message_history = send_res['updated_history']
        convo.save()

        new_limit = service.check_question_limit(convo.message_history)
        return Response({
            'answer': send_res['response'],
            'questions_remaining': new_limit['remaining']
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_conversation(request, conversation_id):
    """
    Get all messages in a conversation
    """
    try:
        convo = get_object_or_404(VideoConversation, id=conversation_id)
        service = ClaudeVideoAnalysisService()
        limit_info = service.check_question_limit(convo.message_history)

        return Response({
            'conversation_id': convo.id,
            'is_initial_analysis': convo.initial_analysis_done,
            'questions_remaining': limit_info['remaining'],
            'messages': convo.message_history
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
