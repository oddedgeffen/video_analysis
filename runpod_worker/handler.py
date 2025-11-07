import runpod

def handler(event):
    """
    Simple test handler
    """
    job_input = event.get('input', {})
    
    return {
        "status": "success",
        "message": "RunPod queue worker is running!",
        "received_input": job_input
    }

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})