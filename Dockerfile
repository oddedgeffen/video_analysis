FROM python:3.10-slim

WORKDIR /app/
COPY runpod/requirements-runpod.txt .

RUN pip install --no-cache-dir -r requirements-runpod.txt

COPY runpod/handler.py .

CMD ["python", "handler.py"]
