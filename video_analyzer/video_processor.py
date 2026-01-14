from pathlib import Path
from django.conf import settings
try:
    from .process_text import analyze_text
    from .process_frames import process_video_segments
    from .process_voice import process_voice_features
    from .utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features, decimal_limit_transcript
except:
    from video_analyzer.process_text import analyze_text
    from video_analyzer.process_frames import process_video_segments
    from video_analyzer.process_voice import process_voice_features
    from video_analyzer.utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features, decimal_limit_transcript

# Import RunPod processing functions
import sys
from pathlib import Path as PathLib
runpod_path = str(PathLib(__file__).parent.parent / 'runpod')
if runpod_path not in sys.path:
    sys.path.insert(0, runpod_path)

# Try to import RunPod processing functions
process_frames_remote = None
try:
    from enpoint import process_frames_remote  # type: ignore
except ImportError:
    # Fallback if runpod module not available
    pass

import logging
logger = logging.getLogger(__name__)

DEBUG = False
USE_RUNPOD = getattr(settings, 'USE_RUNPOD', False)  # Control via Django settings

def process_video_file(paths, video_id=None, use_runpod=None, use_multiprocessing=False):
    """
    Main function to process a video file
    
    Args:
        paths: Dict with 'original_video', 'audio_file', 'base_dir' paths
        video_id: Video ID for S3 key generation (required if using RunPod with S3)
        use_runpod: Override USE_RUNPOD setting (True=remote, False=local, None=use setting)
        use_multiprocessing: Enable multiprocessing for frame processing (auto-detects CPU count)
    """
    # Determine processing mode
    if use_runpod is None:
        use_runpod = USE_RUNPOD
    
    logger.info(f"Processing video file: {paths['original_video']}")
    logger.info(f"Processing mode: {'RunPod (Remote)' if use_runpod else 'Local'}")
    
    ############## process text
    logger.info("Processing text...")
    text_transcript = analyze_text(video_path=paths['original_video'], dst_audio_path=paths['audio_file'], model_size="base", language='en', cleanup=True)    
    save_debug_transcript(text_transcript, 'text_transcript', paths, dbg_local=DEBUG)
    debug_print_text_analysis(text_transcript, dbg_local=DEBUG)

    ############## process frames
    logger.info("Processing frames...")
    frame_interval = int(text_transcript['video_metadata']['fps'])
    if use_runpod:
        # Process on RunPod (remote) #
        if process_frames_remote is None:
            raise ImportError("RunPod module not available. Install runpod requirements.")
        
        logger.info("Using RunPod for frame processing (remote)")
        # frame_interval=60 samples every 2 seconds (2x faster than every 1 second)
        # Increase to 90 for 3x faster (every 3 seconds)
        images_text_transcript = process_frames_remote(
            text_transcript=text_transcript,
            video_url=paths['file_url'],
            frame_interval=frame_interval,
            use_multiprocessing=use_multiprocessing
        )
        logger.info("RunPod processing completed successfully")
    else:
        # Process locally
        logger.info("Using local processing for frames")
        images_text_transcript = process_video_segments(
            text_transcript, 
            paths['original_video'],
            frame_interval=frame_interval,
            use_multiprocessing=use_multiprocessing
        )
    
    save_debug_transcript(images_text_transcript, 'images_text_transcript', paths, dbg_local=DEBUG)

    ############## process voice
    logger.info("Processing voice...")
    voice_images_text_transcript = process_voice_features(images_text_transcript, paths['audio_file'])
    final_transcript = voice_images_text_transcript

    ############## decinal limit the final transcript
    final_transcript = decimal_limit_transcript(final_transcript, 3)
    ############## save debug transcript
    save_debug_transcript(final_transcript, 'final_transcript', paths, dbg_local=DEBUG)
    print_voice_features(final_transcript, dbg_local=DEBUG)
    
    return final_transcript

if __name__ == "__main__":
    from pathlib import Path
    base_dir = Path(r'C:\video_analysis\code\video_analysis_saas\media\uploads')
    paths = {
        'original_video': base_dir / 'original.webm',
        'audio_file': base_dir / 'audio.wav',
        'base_dir': base_dir
            }
    process_video_file(paths)