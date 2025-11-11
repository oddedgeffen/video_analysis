import runpod

def handler(event):
    return {"message": "RunPod worker is alive and working perfectly!"}


runpod.serverless.start({"handler": handler})
