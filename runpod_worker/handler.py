import runpod

def handler(event):
    return {"message": "hello from RunPod"}

runpod.serverless.start({"handler": handler})
