FROM python:3.10-slim

# Install system dependencies for MediaPipe and OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

# Copy requirements and install dependencies
COPY runpod/requirements-runpod.txt .
RUN pip install --no-cache-dir -r requirements-runpod.txt

# Copy handler
COPY runpod/handler.py .

# Copy process_frames from video_analyzer (single source of truth)
COPY video_analyzer/process_frames.py .

CMD ["python", "-u", "handler.py"]
