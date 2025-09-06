import json
import torch
import os
import cv2
from pathlib import Path
from typing import Dict, List, Union, Tuple
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel

def extract_audio(video_path: str, audio_path: str = "temp_audio.wav") -> str:
    """
    Extract audio from video file and save it temporarily
    
    Args:
        video_path: Path to input video file
        audio_path: Path to save temporary audio file
        
    Returns:
        Path to the saved audio file
    """
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, verbose=False, logger=None)
    video.close()
    return audio_path

def transcribe_audio(
    audio_path: str,
    video_path: str,
    model_size: str = "tiny.en",
    language: str = None,
    use_vad: bool = True  # Enable VAD by default now that we have onnxruntime
) -> Tuple[List[Dict[str, Union[float, str]]], str]:
    """
    Transcribe audio file using faster-whisper
    
    Args:
        audio_path: Path to audio file
        model_size: Size of the Whisper model to use
        language: Language code (e.g., 'en' for English) or None for auto-detection
        use_vad: Whether to use Voice Activity Detection (requires onnxruntime)
        
    Returns:
        Tuple of (list of segments, full transcript)
    """
    # Check if CUDA (GPU) is available
    
    device = "cuda"
    compute_type = "float16"
    
    print(f"Using device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # Load model
    # Configure environment for OpenMP
    
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


    # Initialize model with stable settings for GTX 1050
    model = WhisperModel(
        "base",
        device="cuda",          # Use GPU
        compute_type="float32", # Most stable for GTX 1050
        cpu_threads=4,         # Limit CPU threads
        num_workers=1          # Reduce worker threads
    )

      
    # Transcribe with GPU monitoring
    print("\nStarting transcription...")
    
    # Transcribe with conservative settings
    segments, info = model.transcribe(
        "temp_audio.wav",
        language="en",
        beam_size=10,           # Conservative beam size
        vad_filter=False,       # Use VAD to skip silence
        initial_prompt=None,   # No prompt needed
        word_timestamps=True  # Disable word timestamps to save memory
    )

    
    # Process segments
    results = []
    full_text = []
    
    # Get video metadata first (we'll need fps for frame calculations)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    for segment in segments:
        # Calculate frame numbers for this segment
        start_frame = int(segment.start * fps)
        end_frame = int(segment.end * fps)
        
        segment_dict = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "frames": {
                "start_frame": start_frame,
                "end_frame": end_frame,
                "frame_count": end_frame - start_frame
            }
        }
        results.append(segment_dict)
        full_text.append(segment.text.strip())
    
    return results, " ".join(full_text)

def video_to_text(
    video_path: str,
    output_json: str = None,
    model_size: str = "base",
    language: str = None,
    cleanup: bool = True,
    use_vad: bool = False  # Enable VAD by default
) -> Dict[str, Union[List[Dict[str, Union[float, str]]], str]]:
    """
    Extract speech from video and convert to text
    
    Args:
        video_path: Path to input video file
        output_json: Path to save JSON output (optional)
        model_size: Size of the Whisper model to use
        language: Language code or None for auto-detection
        cleanup: Whether to remove temporary audio file
        
    Returns:
        Dictionary containing segments, full transcript, and video metadata
    """
    # Get video metadata
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    cap.release()
    
    # Extract audio
    temp_audio = "temp_audio.wav"
    audio_path = extract_audio(video_path, temp_audio)
    print('audio_path', audio_path)
    # Transcribe
    segments, full_text = transcribe_audio(audio_path, video_path, model_size, language, use_vad)
    
    # Create result dictionary with video metadata
    result = {
        "video_metadata": {
            "fps": fps,
            "total_frames": total_frames,
            "duration_seconds": duration
        },
        "segments": segments,
        "full_text": full_text
    }
    
    # Cleanup temporary audio file
    if cleanup:
        Path(audio_path).unlink(missing_ok=True)
    
    # Log completion
    print("\nTranscription completed successfully!")
    print(f"Number of segments: {len(result['segments'])}")
    
    return result