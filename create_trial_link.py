import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video_analyze.settings')
django.setup()

from video_analyzer.models import TrialLink
from django.utils import timezone

def create_trial_link(max_videos):
    """Create a trial link with specified number of videos"""
    link = TrialLink.objects.create(
        max_videos=max_videos,
        expires_at=timezone.now() + timedelta(days=30)
    )
    return link

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_trial_link.py <number_of_videos>")
        sys.exit(1)
    
    try:
        num_videos = int(sys.argv[1])
        if num_videos <= 0:
            print("Error: Number of videos must be positive")
            sys.exit(1)
        
        link = create_trial_link(num_videos)
        print(f"http://localhost:3000/trial/{link.code}")
        
    except ValueError:
        print("Error: Please provide a valid number")
        sys.exit(1)