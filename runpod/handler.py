import runpod
import os
import tempfile
import requests
import json
import base64

# Import the processing function
from process_frames import process_video_segments


def download_video(video_url: str, temp_dir: str) -> str:
    """Download video from URL to temp directory"""
    print(f"Downloading video from: {video_url}")
    
    video_path = os.path.join(temp_dir, "video.webm")
    
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    
    with open(video_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Video downloaded: {os.path.getsize(video_path)} bytes")
    return video_path


def handler(event):
    """
    RunPod handler for MediaPipe face analysis with GPU acceleration.
    
    Input options:
    1. video_url: URL to download video from (S3, public URL, etc.)
    2. video_base64: Base64 encoded video data
    3. text_transcript: Pre-computed transcript with segments
    4. frame_interval: Sample every Nth frame (default 30)
    
    Example input:
    {
        "input": {
            "video_url": "https://your-bucket.s3.amazonaws.com/video.webm",
            "text_transcript": {
                "video_metadata": {"fps": 30, "frame_width": 640, "frame_height": 480},
                "segments": [{"start": 0, "end": 5, "text": "Hello"}]
            },
            "frame_interval": 30
        }
    }
    """
    try:
        job_input = event.get("input", {})
        
        video_url = job_input.get("video_url")
        video_base64 = job_input.get("video_base64")
        text_transcript = job_input.get("text_transcript")
        frame_interval = job_input.get("frame_interval", 30)
        
        if not video_url and not video_base64:
            return {"error": "Either video_url or video_base64 is required"}
        
        if not text_transcript:
            return {"error": "text_transcript is required (with video_metadata and segments)"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get video file
            if video_url:
                video_path = download_video(video_url, temp_dir)
            else:
                # Decode base64 video
                video_path = os.path.join(temp_dir, "video.webm")
                with open(video_path, 'wb') as f:
                    f.write(base64.b64decode(video_base64))
            
            # Process frames with MediaPipe (GPU-accelerated)
            print("Processing video with MediaPipe...")
            result = process_video_segments(
                text_transcript=text_transcript,
                video_path=video_path,
                frame_interval=frame_interval
            )
            
            print(f"Processing complete! {len(result.get('segments', []))} segments processed")
            return result
            
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == '__main__':
    runpod.serverless.start({"handler": handler})
