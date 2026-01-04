FROM python:3.10-slim

# Install system dependencies for MediaPipe and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/
COPY runpod/requirements-runpod.txt .

RUN pip install --no-cache-dir -r requirements-runpod.txt

COPY runpod/handler.py .
COPY runpod/process_frames.py .

CMD ["python", "-u", "handler.py"]
