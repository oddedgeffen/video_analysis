import runpod

def handler(event):
    # Get the input that was sent
    job_input = event.get("input", {})
    prompt = job_input.get("prompt", "No prompt received")
    
    # Return something based on the input
    return {
        "message": f"I received your prompt: '{prompt}'",
        "received_input": job_input
    }


runpod.serverless.start({"handler": handler})
