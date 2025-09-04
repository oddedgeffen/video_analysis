from django.core.management.base import BaseCommand
import imagehash
from PIL import Image
import os
import logging
from collections import defaultdict

class Command(BaseCommand):
    help = 'Remove duplicate images from a directory based on perceptual hash comparison'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Directory containing images to check')
        parser.add_argument(
            '--threshold',
            type=int,
            default=5,
            help='Hash difference threshold (0-64). Lower values mean more strict comparison. Default is 5.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        directory = options['directory']
        threshold = options['threshold']
        dry_run = options['dry_run']

        if not os.path.exists(directory):
            self.stderr.write(self.style.ERROR(f'Directory {directory} does not exist'))
            return

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Dictionary to store image hashes
        hashes = {}
        # Dictionary to group similar images
        similar_groups = defaultdict(list)

        # Get all image files
        image_files = [f for f in os.listdir(directory) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

        if not image_files:
            self.stdout.write(self.style.WARNING('No image files found in directory'))
            return

        # Calculate hashes for all images
        for filename in image_files:
            filepath = os.path.join(directory, filename)
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

        # Find similar images
        processed = set()
        for filepath1, hash1 in hashes.items():
            if filepath1 in processed:
                continue

            group = [filepath1]
            for filepath2, hash2 in hashes.items():
                if filepath1 != filepath2 and filepath2 not in processed:
                    # Compare hash difference
                    if abs(hash1 - hash2) <= threshold:
                        group.append(filepath2)
                        processed.add(filepath2)

            if len(group) > 1:
                # Keep the first file as original
                similar_groups[group[0]] = group[1:]
                processed.add(filepath1)

        # Report and delete duplicates
        total_duplicates = sum(len(dupes) for dupes in similar_groups.values())
        
        if total_duplicates == 0:
            self.stdout.write(self.style.SUCCESS('No duplicate images found'))
            return

        self.stdout.write(f'Found {total_duplicates} duplicate images:')
        
        for original, duplicates in similar_groups.items():
            self.stdout.write(f'\nOriginal: {os.path.basename(original)}')
            self.stdout.write('Duplicates:')
            for dupe in duplicates:
                self.stdout.write(f'  - {os.path.basename(dupe)}')
                if not dry_run:
                    try:
                        os.remove(dupe)
                        self.stdout.write(self.style.SUCCESS(f'    Deleted: {os.path.basename(dupe)}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    Error deleting {os.path.basename(dupe)}: {str(e)}'))

        action = 'Would delete' if dry_run else 'Deleted'
        self.stdout.write(self.style.SUCCESS(
            f'\n{action} {total_duplicates} duplicate images, kept {len(similar_groups)} originals'
        )) 