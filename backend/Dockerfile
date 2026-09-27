# Контекст сборки - корень репозитория: docker build -f backend/Dockerfile .
FROM node:20-slim AS frontend-build
WORKDIR /srv/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /srv/frontend/dist ./frontend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
