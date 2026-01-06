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
import boto3
from botocore.config import Config
from urllib.parse import urlparse

load_dotenv()

API_KEY = os.getenv("API_KEY")
ENDPOINT_ID = os.getenv("ENDPOINT_ID")


def convert_to_presigned_url(video_url: str, expiration: int = 7200) -> str:
    """
    Convert a regular S3 URL to a presigned URL for temporary access.
    
    Args:
        video_url: Regular S3 URL (e.g., https://bucket.s3.region.amazonaws.com/path/to/video.webm)
        expiration: URL expiration time in seconds (default 2 hours)
    
    Returns:
        Presigned URL that RunPod can access
    """
    # Parse the S3 URL to extract bucket and key
    parsed = urlparse(video_url)
    
    # Handle both formats:
    # 1. https://bucket.s3.region.amazonaws.com/key
    # 2. https://s3.region.amazonaws.com/bucket/key
    if '.s3.' in parsed.netloc or '.s3-' in parsed.netloc:
        # Format 1: bucket.s3.region.amazonaws.com
        bucket_name = parsed.netloc.split('.s3')[0]
        s3_key = parsed.path.lstrip('/')
        
        # Extract region from URL
        region_match = parsed.netloc.split('.s3.')[1] if '.s3.' in parsed.netloc else None
        if region_match:
            region = region_match.split('.amazonaws.com')[0]
        else:
            region = 'us-east-1'  # default
    else:
        # Not an S3 URL, return as-is (might be presigned already or public)
        return video_url
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        region_name=region,
        config=Config(signature_version='s3v4')
    )
    
    # Generate presigned URL
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': s3_key
        },
        ExpiresIn=expiration
    )
    
    print(f"Generated presigned URL (expires in {expiration}s)")
    return presigned_url


def process_frames_remote(
    text_transcript: dict, 
    video_url: str, 
    frame_interval: int = 30,
    use_multiprocessing: bool = True,
    num_workers: int = None
) -> dict:
    """
    Process video frames on RUNPOD endpoint using MediaPipe with multiprocessing.
    Use this to offload heavy GPU processing to the cloud.
    
    Args:
        text_transcript: Dict with video_metadata and segments
        video_url: S3 URL or public URL to video
        frame_interval: Process every Nth frame (default 30)
        use_multiprocessing: Enable parallel frame processing (default True)
        num_workers: Number of worker processes (default auto, max 4)
    
    Returns:
        Dict with processed segments containing face features
    """
    if not API_KEY or not ENDPOINT_ID:
        raise ValueError("API_KEY and ENDPOINT_ID must be set in .env file")
    
    # Convert S3 URL to presigned URL if needed
    video_url = convert_to_presigned_url(video_url)
    
    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "video_url": video_url,
            "text_transcript": text_transcript,
            "frame_interval": frame_interval,
            "use_multiprocessing": use_multiprocessing,
            "num_workers": num_workers
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
    VIDEO_URL = "https://video-analysis-bk.s3.eu-central-1.amazonaws.com/media/uploads/videos/2026_01_04___23_51_57_video-1767563505594/original.webm"
    
    print("Processing video on RunPod...")
    result = process_frames_remote(sample_transcript, VIDEO_URL)
    
    print("\n[SUCCESS] Done!")
    print(f"Processed {len(result.get('segments', []))} segments")
    
    # Save result
    with open("result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Result saved to result.json")
