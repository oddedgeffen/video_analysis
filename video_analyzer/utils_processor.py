from pathlib import Path
from django.conf import settings
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def save_debug_transcript(transcript: dict, dst_filename: str, paths: dict) -> None:
    """
    Save transcript and analysis metadata to debug directory if DEBUG mode is enabled
    
    Args:
        result: Dictionary containing transcript and analysis results
        timestamp: Timestamp string for filename
    """
    if not settings.DEBUG:
        return
    dst_path = paths['base_dir'].joinpath(f'{dst_filename}.json')
    logger.info(f"Debug mode: Saving transcript to {dst_path}")
    
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

def debug_print_text_analysis(result: dict) -> None:
    """
    Print detailed analysis information in debug mode
    
    Args:
        result: Dictionary containing transcript and analysis results
    """
    if not settings.DEBUG:
        return
        
    logger.info("\n=== Video Analysis Debug Information ===")
    
    # Print video metadata
    if "video_metadata" in result:
        logger.info("\nVideo Metadata:")
        logger.info(f"Duration: {result['video_metadata'].get('duration_seconds', 0):.2f} seconds")
        logger.info(f"FPS: {result['video_metadata'].get('fps', 0)}")
        logger.info(f"Total Frames: {result['video_metadata'].get('total_frames', 0)}")
    
    # Print transcript statistics
    logger.info("\nTranscript Statistics:")
    logger.info(f"Number of segments: {len(result.get('segments', []))}")
    total_words = len(result.get('full_text', '').split())
    logger.info(f"Total words: {total_words}")
    
    # Print full transcript with clear formatting
    logger.info("\nFull Transcript:")
    logger.info("=" * 80)
    logger.info(result.get('full_text', 'No transcript available'))
    logger.info("=" * 80)
    
    # Print segment details
    if result.get('segments'):
        logger.info("\nSegment Details:")
        for i, segment in enumerate(result['segments'], 1):
            logger.info(f"\nSegment {i}:")
            logger.info(f"Start: {segment.get('start', 0):.2f}s")
            logger.info(f"End: {segment.get('end', 0):.2f}s")
            logger.info(f"Text: {segment.get('text', '')}")