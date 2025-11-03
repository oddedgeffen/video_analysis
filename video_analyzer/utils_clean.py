import boto3
from django.conf import settings
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

def _delete_processing_folder(paths: dict) -> None:
    """
    Delete the processing folder for a video.
    """
    try:
        base_dir = paths['base_dir']
        if base_dir.exists():
            shutil.rmtree(base_dir, ignore_errors=True)
            logger.info(f"Deleted local processing directory '{base_dir}")
    except Exception as e:
        logger.error(f"Failed deleting local processing directory: {e}")
