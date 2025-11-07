FROM python:3.10-slim

WORKDIR /app
COPY requirements-runpod.txt .

RUN pip install --no-cache-dir -r requirements-runpod.txt

COPY handler.py .

CMD ["python", "handler.py"]
