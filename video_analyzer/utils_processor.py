from pathlib import Path
from django.conf import settings
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def decimal_limit_transcript(transcript: dict, limit: int) -> dict:
    """
    Limit decimal places in transcript to reduce file size and improve readability.
    Recursively processes all nested dictionaries and lists.
    
    Args:
        transcript: Dictionary containing transcript data with numerical values
        limit: Number of decimal places to keep (e.g., 3 for 0.123)
    
    Returns:
        Modified transcript with limited decimal places
        
    Example:
        >>> data = {"value": 0.123456789, "nested": {"val": 1.987654321}}
        >>> decimal_limit_transcript(data, 3)
        {"value": 0.123, "nested": {"val": 1.988}}
    """
    if isinstance(transcript, dict):
        return {key: decimal_limit_transcript(value, limit) for key, value in transcript.items()}
    elif isinstance(transcript, list):
        return [decimal_limit_transcript(item, limit) for item in transcript]
    elif isinstance(transcript, float):
        return round(transcript, limit)
    else:
        # Return as-is for int, str, bool, None, etc.
        return transcript

def save_debug_transcript(transcript: dict, dst_filename: str, paths: dict, dbg_local=False) -> None:
    """
    Save transcript and analysis metadata to debug directory if DEBUG mode is enabled
    
    Args:
        result: Dictionary containing transcript and analysis results
        timestamp: Timestamp string for filename
    """
    if not dbg_local:
        if not settings.DEBUG:
            return
    dst_path = paths['base_dir'].joinpath(f'{dst_filename}.json')
    logger.info(f"Debug mode: Saving transcript to {dst_path}")
    
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

def debug_print_text_analysis(result: dict, dbg_local=False) -> None:
    """
    Print detailed analysis information in debug mode
    
    Args:
        result: Dictionary containing transcript and analysis results
    """
    
    if not dbg_local:
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

def print_voice_features(enriched_transcript, dbg_local=False):
    if not dbg_local:
        if not settings.DEBUG:
            return
    print("\nSegment statistics:")
    for i, segment in enumerate(enriched_transcript['segments']):
        print(f"\nSegment {i+1}:")
        print(f"Text: {segment['text'][:50]}...")
        print(f"Duration: {segment['end'] - segment['start']:.1f}s")
        print(f"Speaking rate: {segment['voice_features']['rate']['words_per_minute']:.1f} words/min")
        print(f"Flags: {', '.join(k for k, v in segment['voice_features']['derived_flags'].items() if v)}")

    # Print summary of available features
    print("\nEnriched transcript now contains:")
    print("- Visual features (face analysis)")
    print("- Voice features:")
    print("  - Energy metrics (RMS, dB)")
    print("  - Pitch statistics (F0)")
    print("  - Speaking rate")
    print("  - Pause analysis")
    print("  - Spectral features")
    print("  - Voice quality metrics")
    print("  - Derived flags (too_quiet, monotone, too_fast, choppy)")