import os
from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from logo_saas.storage import StaticStorage


class Command(BaseCommand):
    help = 'Collect static files and upload them directly to S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_true',
            help='Do NOT prompt the user for input of any kind.'
        )

    def handle(self, *args, **options):
        # Use our S3 storage directly
        s3_storage = StaticStorage()
        self.stdout.write(f"S3 storage initialized with location: {s3_storage.location}")
        
        # Find all static files
        found_files = []
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                found_files.append(path)
                
        self.stdout.write(f"Found {len(found_files)} static files")
        
        # Upload each file to S3
        success = 0
        for path in found_files:
            try:
                file_path = finders.find(path)
                if file_path:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        name = s3_storage.save(path, ContentFile(content))
                        success += 1
                        self.stdout.write(f"Uploaded: {path} -> {name}")
            except Exception as e:
                self.stderr.write(f"Error uploading {path}: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully uploaded {success} of {len(found_files)} files to S3'
        )) 