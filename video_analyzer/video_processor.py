from django.conf import settings
try:
    from .process_text import analyze_text
    from .process_frames import process_video_segments
    from .process_voice import process_voice_features
    from .utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features
except:
    from video_analyzer.process_text import analyze_text
    from video_analyzer.process_frames import process_video_segments
    from video_analyzer.process_voice import process_voice_features
    from video_analyzer.utils_processor import save_debug_transcript, debug_print_text_analysis, print_voice_features

DEBUG = False

def process_video_file(paths):
    """Main function to process a video file"""

    ############## process text    
    text_transcript = analyze_text(video_path=paths['original_video'], dst_audio_path=paths['audio_file'], model_size="base", language='en', cleanup=True)    
    save_debug_transcript(text_transcript, 'text_transcript', paths, dbg_local=DEBUG)
    debug_print_text_analysis(text_transcript, dbg_local=DEBUG)

    ############## process frames
    images_text_transcript = process_video_segments(text_transcript, paths['original_video'])
    save_debug_transcript(images_text_transcript, 'images_text_transcript', paths, dbg_local=DEBUG)

    ############## process voice
    voice_images_text_transcript = process_voice_features(images_text_transcript, paths['audio_file'])
    final_transcript = voice_images_text_transcript
    save_debug_transcript(final_transcript, 'final_transcript', paths, dbg_local=DEBUG)
    print_voice_features(final_transcript, dbg_local=DEBUG)
    
    return final_transcript

if __name__ == "__main__":
    from pathlib import Path
    base_dir = Path(r'C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_11___09_11_24_video-1757571071875')
    paths = {
        'original_video': base_dir / 'original.webm',
        'audio_file': base_dir / 'audio.wav',
        'base_dir': base_dir
            }
    process_video_file(paths)