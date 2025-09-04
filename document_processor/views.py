from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import ProcessedDocument, Feedback
from .serializers import ProcessedDocumentSerializer, FeedbackSerializer
from .logo_replacer import replace_logo, ensure_dir_exists
import os, tempfile
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
from rest_framework.decorators import api_view, permission_classes, action
import threading
from django.http import HttpResponse, FileResponse
import mimetypes
import boto3
from botocore.exceptions import ClientError
import re
import tempfile, shutil
from django.core.files.base import File
import logging
from .image_extraction import extract_images_from_document
import base64
from PIL import Image
import imagehash

# Maximum file size (25MB in bytes)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

def validate_file_size(file_obj, max_size=MAX_FILE_SIZE):
    """Validate if file size is within limits."""
    if file_obj.size > max_size:
        raise ValueError(f"File size exceeds the maximum limit of {max_size/1024/1024}MB")

# Create your views here.

def ensure_media_dirs():
    """Ensure all required media directories exist"""
    dirs = [
        os.path.join(settings.MEDIA_ROOT, 'documents', 'original'),
        os.path.join(settings.MEDIA_ROOT, 'documents', 'processed'),
        os.path.join(settings.MEDIA_ROOT, 'logos', 'old'),
        os.path.join(settings.MEDIA_ROOT, 'logos', 'new'),
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

class ProcessedDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProcessedDocument.objects.all().order_by('-created_at')
    serializer_class = ProcessedDocumentSerializer
    logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        self.logger.info("Starting document upload process")
        self.logger.info(f"Storage backend: {'S3' if settings.USE_S3 else 'Local'}")
        
        # Validate file sizes before processing
        try:
            original_doc = request.data.get('original_document')
            old_logo = request.data.get('old_logo')
            new_logo = request.data.get('new_logo')
            
            if original_doc:
                validate_file_size(original_doc)
            if old_logo:
                validate_file_size(old_logo)
            if new_logo:
                validate_file_size(new_logo)
                
        except ValueError as e:
            self.logger.warning(f"File size validation failed: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure media directories exist
        ensure_media_dirs()
        
        # Create initial document record in 'processing' state
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Log file information before saving
        self.logger.info(f"Original document: {getattr(original_doc, 'name', 'unknown')}")
        self.logger.info(f"Old logo: {getattr(old_logo, 'name', 'unknown')}")
        self.logger.info(f"New logo: {getattr(new_logo, 'name', 'unknown')}")
        
        document = serializer.save(status='processing')
        self.logger.info(f"Created document record with ID: {document.id}")

        # Launch background thread to process the document asynchronously
        thread = threading.Thread(
            target=self._async_process,
            args=(document.id,),
            daemon=True
        )
        thread.start()
        self.logger.info(f"Started processing thread for document ID: {document.id}")
        
        # Immediately return the document in processing state
        return Response(self.get_serializer(document).data, status=status.HTTP_201_CREATED)

    def _async_process(self, document_id):
        logger = logging.getLogger(__name__)
        logger.info(f"Starting async processing for document ID: {document_id}")
        
        doc = ProcessedDocument.objects.get(id=document_id)
        logger.info(f"Document details - Original: {doc.original_document.name}, Old logo: {doc.old_logo.name}, New logo: {doc.new_logo.name}")

        tmpdir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {tmpdir}")
        
        try:
            def to_local(fieldfile, fname):
                local_path = os.path.join(tmpdir, fname)
                with fieldfile.open("rb") as src, open(local_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                logger.info(f"Copied {fieldfile.name} to {local_path}")
                return local_path

            # Get original file extension
            doc_path = to_local(doc.original_document, os.path.basename(doc.original_document.name))
            old_logo = to_local(doc.old_logo, os.path.basename(doc.old_logo.name))
            new_logo = to_local(doc.new_logo, os.path.basename(doc.new_logo.name))

            logger.info("Starting logo replacement process")
            processed_path = replace_logo(doc_path, old_logo, new_logo)
            logger.info(f"Logo replacement completed, processed file at: {processed_path}")
            
            if not os.path.exists(processed_path):
                raise FileNotFoundError(f"Processed file not found: {processed_path}")

            with open(processed_path, "rb") as f:
                filename = os.path.basename(processed_path)
                # Let Django handle the file storage
                logger.info(f"Saving processed document with filename: {filename}")
                doc.processed_document.save(filename, File(f), save=False)
                doc.status = "completed"
                                
                if doc.original_document:
                    try:
                        doc.original_document.delete(save=False)
                        doc.original_document = None
                        logger.info(f"Deleted original document for {document_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete original document: {str(e)}")
                
                if doc.old_logo:
                    try:
                        doc.old_logo.delete(save=False)
                        doc.old_logo = None
                        logger.info(f"Deleted old logo for {document_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete old logo: {str(e)}")
                
                if doc.new_logo:
                    try:
                        doc.new_logo.delete(save=False)
                        doc.new_logo = None
                        logger.info(f"Deleted new logo for {document_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete new logo: {str(e)}")
                
                doc.save()
                logger.info(f"Successfully saved processed document. Storage path: {doc.processed_document.name}")
                
                if settings.USE_S3:
                    logger.info(f"S3 storage path should be: media/{doc.processed_document.name}")

        except Exception as e:
            logger.error(f"Processing failed for document {document_id}: {str(e)}", exc_info=True)
            doc.status = "failed"
            doc.error_message = str(e)
            doc.save()

        finally:
            logger.info(f"Cleaning up temporary directory: {tmpdir}")
            shutil.rmtree(tmpdir, ignore_errors=True)
            logger.info(f"Async processing completed for document {document_id} with status: {doc.status}")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        from django.conf import settings
        import boto3, os, mimetypes

        logger = logging.getLogger(__name__)
        logger.info(f"Download request received for document ID: {pk}, Method: {request.method}")
        
        try:
            doc = self.get_object()
            logger.info(f"Document status: {doc.status}")
            logger.info(f"Document storage backend: {'S3' if settings.USE_S3 else 'Local'}")

            if doc.status != "completed" or not doc.processed_document:
                logger.warning(f"Document not ready for download. Status: {doc.status}, Has processed file: {bool(doc.processed_document)}")
                return Response(
                    {"detail": "No processed document available for download."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get filename from the name attribute, not the path
            filename = os.path.basename(doc.processed_document.name)
            logger.info(f"Filename: {filename}")
            logger.info(f"Full document name: {doc.processed_document.name}")

            # Guess content type
            mime, _ = mimetypes.guess_type(filename)
            content_type = mime or "application/octet-stream"
            logger.info(f"Content type: {content_type}")

            def delete_local_file_with_retry(doc_id):
                """Helper function to delete local file with retries"""
                import time
                time.sleep(10)
                max_attempts = 30  # Maximum number of attempts
                retry_delay = 3    # Seconds between attempts
                attempts = 0
                
                while attempts < max_attempts:
                    try:
                        # Refresh the document instance to avoid stale data
                        doc = ProcessedDocument.objects.get(id=doc_id)
                        
                        # Try to delete the file
                        doc.processed_document.delete(save=False)
                        doc.processed_document = None
                        doc.status = "downloaded"
                        doc.save()
                        logger.info(f"Successfully deleted local file for document {doc_id}")
                        return
                    except PermissionError as e:
                        # File is still being accessed
                        attempts += 1
                        if attempts < max_attempts:
                            logger.info(f"File still in use, attempt {attempts}/{max_attempts}. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            logger.warning(f"Could not delete local file for document {doc_id} after {max_attempts} attempts: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Unexpected error deleting document {doc_id}: {str(e)}")
                        return

            # Check if we're using S3 storage
            if settings.USE_S3:
                try:
                    s3 = boto3.client(
                        "s3",
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME,
                    )

                    # Get the S3 key
                    s3_key = f"media/{doc.processed_document.name}"
                    logger.info(f"S3 key for download: {s3_key}")

                    # Generate presigned URL
                    url = s3.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                            "Key": s3_key,
                            "ResponseContentDisposition": f'attachment; filename="{filename}"',
                            "ResponseContentType": content_type,
                        },
                        ExpiresIn=300,  # 5 minutes
                    )
                    logger.info("Successfully generated presigned URL")

                    # Start background thread to delete file after delay
                    thread = threading.Thread(
                        target=delete_local_file_with_retry,
                        args=(doc.id,),
                        daemon=True
                    )
                    thread.start()
                    logger.info(f"Started background deletion thread for document {doc.id}")

                    return Response({"download_url": url})

                except Exception as e:
                    logger.error(f"S3 error: {str(e)}", exc_info=True)
                    return Response(
                        {"detail": f"Failed to generate S3 download link: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                # Local storage download
                try:
                    file_path = doc.processed_document.path
                    logger.info(f"Local file path: {file_path}")
                    
                    if not os.path.exists(file_path):
                        logger.error(f"Local file not found: {file_path}")
                        return Response(
                            {"detail": "File not found in local storage."},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    # Create response with file
                    response = FileResponse(
                        open(file_path, 'rb'),
                        content_type=content_type,
                        as_attachment=True,
                        filename=filename
                    )

                    # Only start deletion thread if file was actually sent
                    thread = threading.Thread(
                        target=delete_local_file_with_retry,
                        args=(doc.id,),
                        daemon=True
                    )
                    thread.start()
                    logger.info(f"Started background deletion thread for document {doc.id}")

                    return response

                except ValueError as e:
                    logger.error(f"Path access error: {str(e)}", exc_info=True)
                    return Response(
                        {"detail": "Error accessing file path."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

        except Exception as e:
            logger.error(f"Unexpected error in download view: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An unexpected error occurred while processing your download request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
def submit_feedback(request):
    serializer = FeedbackSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_all_feedback(request):
    feedback = Feedback.objects.all().order_by('-created_at')
    serializer = FeedbackSerializer(feedback, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def extract_document_images(request):
    """
    Extract images from an uploaded document and remove duplicates.
    Returns a list of base64-encoded images found in the document.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting image extraction process")
    
    if 'document' not in request.FILES:
        return Response(
            {"error": "No document provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    document = request.FILES['document']
    
    # Validate file size
    try:
        validate_file_size(document)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    upload_dir = None
    extraction_dir = None
    
    try:
        # Create a temporary directory for the uploaded document
        upload_dir = tempfile.mkdtemp()
        
        # Save uploaded file to temporary directory
        temp_path = os.path.join(upload_dir, document.name)
        with open(temp_path, 'wb') as temp_file:
            for chunk in document.chunks():
                temp_file.write(chunk)
        
        # Extract images - now returns (images, temp_dir)
        image_paths, extraction_dir = extract_images_from_document(temp_path)
        
        if not image_paths:
            return Response(
                {"error": "No images found in document"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Remove duplicates using perceptual hashing
        hashes = {}
        unique_images = []
        del_images = []
        threshold = 5  # Hash difference threshold (lower = more strict)
        processed = set()
        
        # Calculate hashes for all images
        for filepath in image_paths:
            try:
                with Image.open(filepath) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    # Calculate perceptual hash
                    hash = imagehash.average_hash(img)
                    hashes[filepath] = hash
            except Exception as e:
                logger.error(f'Error processing {filepath}: {str(e)}')
                continue

        # Find unique images
        for filepath1, hash1 in hashes.items():
            if filepath1 in del_images:
                continue

            for filepath2, hash2 in hashes.items():
                if filepath1 != filepath2:
                    # Compare hash difference
                    if abs(hash1 - hash2) <= threshold:
                        del_images.append(filepath2)

        unique_images = [img for img in image_paths if img not in del_images]

        logger.info(f"Found {len(image_paths)} total images, {len(unique_images)} unique images")
        

        # Delete duplicate images
        for img_path in del_images:
            try:
                os.unlink(img_path)
                logger.info(f"Deleted duplicate image: {img_path}")
            except Exception as e:
                logger.error(f"Error deleting duplicate image {img_path}: {str(e)}")

        # Convert unique images to base64
        base64_images = []
        for img_path in unique_images:
            try:
                with open(img_path, 'rb') as img_file:
                    img_data = img_file.read()
                    base64_data = base64.b64encode(img_data).decode('utf-8')
                    base64_images.append(f"data:image/png;base64,{base64_data}")
            except Exception as e:
                logger.error(f"Error processing image {img_path}: {str(e)}")
        
        return Response({
            "images": base64_images,
            "total_images": len(image_paths),
            "unique_images": len(base64_images),
            "duplicates_removed": len(image_paths) - len(base64_images)
        })
        
    except Exception as e:
        logger.error(f"Error during image extraction: {str(e)}")
        return Response(
            {"error": "Error processing document"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up all temporary directories
        if upload_dir:
            try:
                shutil.rmtree(upload_dir)
                logger.info("Cleaned up upload directory")
            except Exception as e:
                logger.error(f"Error cleaning up upload directory: {str(e)}")
        
        if extraction_dir:
            try:
                shutil.rmtree(extraction_dir)
                logger.info("Cleaned up extraction directory")
            except Exception as e:
                logger.error(f"Error cleaning up extraction directory: {str(e)}")
