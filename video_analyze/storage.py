# video_analyze/storage.py
from storages.backends.s3boto3 import S3Boto3Storage
import mimetypes
import os
import logging

logger = logging.getLogger(__name__)

class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = None  # Remove explicit ACL, rely on bucket policy
    file_overwrite = True

class MediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = None  # Remove explicit ACL, rely on bucket policy
    querystring_auth = True 
    file_overwrite = False
    
    def _get_content_type(self, name):
        """
        Guess the content type for video/audio/transcript artifacts.
        Provides explicit mappings for common media we generate/use.
        """
        extension = os.path.splitext(name)[1].lower()

        # Explicit media mappings for this project
        if extension == '.webm':
            return 'video/webm'
        if extension == '.mp4':
            return 'video/mp4'
        if extension == '.wav':
            return 'audio/wav'
        if extension == '.json':
            return 'application/json'

        # Fallback to mimetypes
        content_type, _ = mimetypes.guess_type(name)
        return content_type or 'application/octet-stream'
        
    def _save(self, name, content):
        """
        Override _save to set the correct content type and log the S3 save
        """
        content_type = self._get_content_type(name)
        content.content_type = content_type
        logger.info(f"S3 MediaStorage: uploading '{name}' with Content-Type '{content_type}'")
        saved_name = super()._save(name, content)
        logger.info(f"S3 MediaStorage: saved as '{saved_name}'")
        return saved_name

    def path(self, name):
        """
        Return None for path operations since S3 doesn't support absolute paths
        """
        return None
