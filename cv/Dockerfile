# Контекст - корень репозитория; веса и индекс приезжают томом /assets
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/assets/models/hf \
    TORCH_HOME=/assets/models/torch-hub \
    HF_HUB_OFFLINE=1 \
    YOLO_OFFLINE=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY cv/requirements.txt .
RUN pip install -r requirements.txt

COPY cv/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
