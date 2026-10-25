FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /workspace/backend
CMD ["python","-m","uvicorn","main:app","--app-dir","backend","--host","0.0.0.0","--port","8000"]
