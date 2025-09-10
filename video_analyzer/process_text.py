import torch
import os
import cv2
from pathlib import Path
from fractions import Fraction
from typing import Dict, List, Union, Tuple
from faster_whisper import WhisperModel
import subprocess
from pathlib import Path
import imageio_ffmpeg as im_ffmpeg
import librosa

def extract_audio(video_path: str, audio_path: str = "temp_audio.wav") -> str:
    """
    Extract audio from video file using imageio-ffmpeg's bundled executable
    """
    
    
    try:
        # Get the bundled im_ffmpeg executable path
        im_ffmpeg_exe = im_ffmpeg.get_ffmpeg_exe()
        
        # Ensure output directory exists
        Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg command
        cmd = [
            im_ffmpeg_exe,
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # WAV format
            '-ar', '16000',  # Sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            audio_path
        ]
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")
        
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file was not created: {audio_path}")
            
        print(f"Successfully extracted audio to {audio_path}")
        
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        raise

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
        audio_path,
        language="en",
        beam_size=10,           # Conservative beam size
        vad_filter=use_vad,       # Use VAD to skip silence
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

def get_video_info(video_path, dst_audio_path):
    
    duration = librosa.get_duration(path=dst_audio_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    total_frames = 0
    while True:
        ret, frame = cap.read()
        if total_frames == 0:
            frame_height, frame_width = frame.shape[:2]
        if not ret:
            break
        total_frames += 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
    fps = int(total_frames / duration)
    cap.release()
    return fps, total_frames, duration, frame_width, frame_height


def analyze_text(
    video_path: str,
    dst_audio_path: str,
    model_size: str = "base",
    language: str = None,
    cleanup: bool = True,
    use_vad: bool = False  # Enable VAD by default
) -> Dict[str, Union[List[Dict[str, Union[float, str]]], str]]:
    """
    Extract speech from video and convert to text
    
    Args:
        video_path: Path to input video file
        model_size: Size of the Whisper model to use
        language: Language code or None for auto-detection
        cleanup: Whether to remove temporary audio file
        
    Returns:
        Dictionary containing segments, full transcript, and video metadata
    """

    extract_audio(video_path, dst_audio_path)
    print('audio_path', dst_audio_path)
    fps, total_frames, duration, frame_width, frame_height = get_video_info(video_path, dst_audio_path)
    segments, full_text = transcribe_audio(dst_audio_path, video_path, model_size, language, use_vad)
    
    # Create result dictionary with video metadata
    result = {
        "video_metadata": {
            "fps": fps,
            "total_frames": total_frames,
            "duration_seconds": duration,
            "frame_width": frame_width,
            "frame_height": frame_height
        },
        "segments": segments,
        "full_text": full_text
    }
    
    
    # Log completion
    print("\nTranscription completed successfully!")
    print(f"Number of segments: {len(result['segments'])}")
    
    return result

if __name__ == "__main__":
    video_path = r"C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\original.webm"
    audio_path = r"C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\audio.wav"
    result = analyze_text(video_path=video_path,
        dst_audio_path=audio_path,
        model_size="base",
        language='en',
        cleanup=True)
    import json
    with open(r'media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\text_transcript.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
