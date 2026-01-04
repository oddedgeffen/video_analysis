"""
RunPod Client - Process video frames locally OR on RunPod endpoint

Usage:
    # Option 1: Run locally
    result = process_frames_local(text_transcript, video_path)
    
    # Option 2: Run on RunPod (GPU cloud)
    result = process_frames_remote(text_transcript, video_url)
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
ENDPOINT_ID = os.getenv("ENDPOINT_ID")


def process_frames_local(text_transcript: dict, video_path: str, frame_interval: int = 30) -> dict:
    """
    Process video frames LOCALLY using MediaPipe.
    Use this when you have a GPU locally or for testing.
    """
    from video_analyzer.process_frames import process_video_segments
    return process_video_segments(text_transcript, video_path, frame_interval)


def process_frames_remote(text_transcript: dict, video_url: str, frame_interval: int = 30) -> dict:
    """
    Process video frames on RUNPOD endpoint using MediaPipe.
    Use this to offload heavy GPU processing to the cloud.
    
    Args:
        text_transcript: Dict with video_metadata and segments
        video_url: Public URL to download video (S3 presigned, public URL, etc.)
        frame_interval: Process every Nth frame (default 30)
    
    Returns:
        Dict with processed segments containing face features
    """
    if not API_KEY or not ENDPOINT_ID:
        raise ValueError("API_KEY and ENDPOINT_ID must be set in .env file")
    
    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "video_url": video_url,
            "text_transcript": text_transcript,
            "frame_interval": frame_interval
        }
    }
    
    # Submit job
    print(f"Submitting video to RunPod for processing...")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    job_data = response.json()
    
    job_id = job_data.get("id")
    if not job_id:
        raise RuntimeError(f"Failed to start job: {job_data}")
    
    print(f"Job ID: {job_id}")
    
    # Poll for status
    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
    
    while True:
        status_resp = requests.get(status_url, headers=headers)
        data = status_resp.json()
        
        status = data.get("status")
        print(f"Status: {status}")
        
        if status == "COMPLETED":
            output = data.get("output")
            if isinstance(output, dict) and "error" in output:
                raise RuntimeError(f"Processing failed: {output['error']}")
            return output
            
        elif status in ["FAILED", "CANCELLED"]:
            raise RuntimeError(f"Job failed: {data}")
        
        time.sleep(3)


# ============ TEST / DEMO ============
if __name__ == "__main__":
    # Example: Test the remote processing
    
    # Sample transcript (you'd normally get this from process_text.py)
    sample_transcript = {
        "video_metadata": {
            "fps": 30,
            "frame_width": 640,
            "frame_height": 480,
            "duration_seconds": 5.0
        },
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is a test."},
            {"start": 2.5, "end": 5.0, "text": "Testing the endpoint."}
        ]
    }
    
    # Replace with your actual video URL
    VIDEO_URL = "https://your-bucket.s3.amazonaws.com/video.webm"
    
    print("Processing video on RunPod...")
    result = process_frames_remote(sample_transcript, VIDEO_URL)
    
    print("\n✅ Done!")
    print(f"Processed {len(result.get('segments', []))} segments")
    
    # Save result
    with open("result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Result saved to result.json")
