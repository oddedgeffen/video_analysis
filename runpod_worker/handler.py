import runpod
import cv2
import mediapipe as mp
import tempfile
import requests
import os
import json

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def process_video(video_url):
    # download video
    r = requests.get(video_url, stream=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    for chunk in r.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()

    cap = cv2.VideoCapture(tmp.name)
    frame_count = 0
    detections = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 3 != 0:
            continue  # skip frames for speed

        frame = cv2.resize(frame, (640, 360))
        results = mp_face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.multi_face_landmarks:
            detections.append(len(results.multi_face_landmarks))

    cap.release()
    os.unlink(tmp.name)

    return {
        "frames_processed": frame_count,
        "detections_count": len(detections)
    }

def handler(event):
    video_url = event["input"].get("video_url")
    return process_video(video_url)

runpod.serverless.start({"handler": handler})
