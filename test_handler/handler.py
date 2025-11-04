import runpod

def handler(event):
    return {"status": "success", "message": "Hello from RunPod!"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})

