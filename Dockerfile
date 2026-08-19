FROM python:3.11-slim

WORKDIR /app

# System deps for matplotlib, chromadb
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY data/ ./data/

# Copy built frontend (must run: cd frontend && npm run build first)
COPY frontend/dist/ ./frontend/dist/

# Create necessary directories
RUN mkdir -p uploads backend/charts chroma_db

# Copy env example (actual .env must be mounted or passed via environment)
COPY .env.example .env.example

EXPOSE 5050

ENV PYTHONPATH=/app/backend
ENV PORT=5050

CMD ["python", "backend/app.py"]
