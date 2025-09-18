# video_analyze/storage.py
from storages.backends.s3boto3 import S3Boto3Storage
import mimetypes
import os

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
        Guess the content type of a file based on its extension.
        Add explicit mappings for common document types.
        """
        content_type, encoding = mimetypes.guess_type(name)
        
        # Add explicit mappings for Office documents
        extension = os.path.splitext(name)[1].lower()
        if extension == '.docx':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif extension == '.xlsx':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif extension == '.pptx':
            return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif extension == '.pdf':
            return 'application/pdf'
            
        return content_type or 'application/octet-stream'
        
    def _save(self, name, content):
        """
        Override _save to set the correct content type
        """
        content.content_type = self._get_content_type(name)
        return super()._save(name, content)

    def path(self, name):
        """
        Return None for path operations since S3 doesn't support absolute paths
        """
        return None
