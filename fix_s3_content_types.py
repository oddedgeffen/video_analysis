#!/usr/bin/env python
"""
Script to fix content types of existing files in S3 bucket.
Run this after updating the MediaStorage class.
"""
import os
import boto3
import mimetypes
from django.conf import settings
import django

# Initialize Django to access settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video_analyze.settings')
django.setup()

# Get S3 credentials from Django settings
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_S3_REGION_NAME = settings.AWS_S3_REGION_NAME

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)

# Map of file extensions to MIME types
MIME_TYPES = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.pdf': 'application/pdf',
}

def get_content_type(key):
    """Get the appropriate content type for a file"""
    ext = os.path.splitext(key)[1].lower()
    if ext in MIME_TYPES:
        return MIME_TYPES[ext]
    
    # Fall back to mimetypes library
    content_type, _ = mimetypes.guess_type(key)
    return content_type or 'application/octet-stream'

def fix_content_types():
    """Fix content types for all objects in the bucket"""
    print(f"Fixing content types in bucket: {AWS_STORAGE_BUCKET_NAME}")
    
    # List all objects in the media folder
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix='media/')
    
    fixed_count = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            
            # Skip directories
            if key.endswith('/'):
                continue
                
            # Get current content type
            response = s3.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=key)
            current_content_type = response.get('ContentType', '')
            
            # Determine correct content type
            correct_content_type = get_content_type(key)
            
            # If content type is wrong, fix it
            if current_content_type != correct_content_type and correct_content_type:
                print(f"Updating {key}: {current_content_type} -> {correct_content_type}")
                
                # Copy object to itself with new metadata
                s3.copy_object(
                    Bucket=AWS_STORAGE_BUCKET_NAME,
                    CopySource={'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': key},
                    Key=key,
                    MetadataDirective='REPLACE',
                    ContentType=correct_content_type,
                    Metadata=response.get('Metadata', {})
                )
                fixed_count += 1
    
    print(f"Fixed {fixed_count} objects")

if __name__ == "__main__":
    fix_content_types() 