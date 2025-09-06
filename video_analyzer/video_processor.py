from pathlib import Path
from django.conf import settings
import json
from .process_text import video_to_text

def process_video_file(video_path):
    """Main function to process a video file"""
    # Get filename without extension for result naming
    timestamp = Path(video_path).stem
    
    # Process video without saving transcript (process_text will return results only)
    result = video_to_text(
        video_path=video_path,
        output_json=None,  # Don't save in process_text
        model_size="base",
        language='en',
        cleanup=True
    )
    
    # Save transcript only in debug mode
    if settings.DEBUG:
        debug_transcript_path = Path(settings.MEDIA_ROOT) / 'debug' / 'transcripts'
        debug_transcript_path.mkdir(parents=True, exist_ok=True)
        
        transcript_file = debug_transcript_path / f'transcript_{timestamp}.json'
        print(f"Debug mode: Saving transcript to {transcript_file}")
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result