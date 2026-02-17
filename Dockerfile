# Stage 1: Build frontend
FROM node:24-slim AS frontend
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Copy pipeline configs (recipes, etc.)
COPY configs/ ./configs/

# Copy frontend build from stage 1
COPY --from=frontend /app/ui/dist ./static/

# Create output directory (overlaid by persistent volume in production)
RUN mkdir -p /app/output

# Run as non-root user
RUN addgroup --system --gid 1001 cineforge && \
    adduser --system --uid 1001 --gid 1001 cineforge && \
    chown -R cineforge:cineforge /app
USER cineforge

ENV PYTHONPATH=/app/src
ENV CINEFORGE_STATIC_DIR=/app/static

EXPOSE 8000
CMD ["uvicorn", "cine_forge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
