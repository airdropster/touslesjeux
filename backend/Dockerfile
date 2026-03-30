# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_KEY=changeme
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

# Stage 2: Install Python dependencies
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 3: Production image
FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=backend-builder /usr/local/bin/alembic /usr/local/bin/alembic
COPY backend/app/ app/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .

# Copy frontend build from stage 1
COPY --from=frontend-builder --chown=appuser:appuser /app/dist static/

USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
