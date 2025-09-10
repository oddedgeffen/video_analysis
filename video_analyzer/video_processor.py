from django.conf import settings
from .process_text import analyze_text
from .process_frames import process_video_segments
from .utils_processor import save_debug_transcript, debug_print_text_analysis


def process_video_file(paths):
    """Main function to process a video file"""

    # process text    
    # Process video without saving transcript (process_text will return results only)
    trainscript_1 = analyze_text(
        video_path=paths['original_video'],
        dst_audio_path=paths['audio_file'],
        model_size="base",
        language='en',
        cleanup=True
    )
    
    # Save text transcript if in DEBUG mode
    save_debug_transcript(trainscript_1, 'text_transcript', paths)
    debug_print_text_analysis(trainscript_1)


    # process frames
    trainscript_2 = process_video_segments(trainscript_1, paths)
    return 1