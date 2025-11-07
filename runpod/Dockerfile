FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your handler
COPY handler.py .

# Run the worker
CMD ["python", "handler.py"]
