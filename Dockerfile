FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-server.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy application code
COPY server.py .
COPY scripts/ scripts/
COPY match-form.html .
COPY config.json .
COPY static/ static/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PORT=8080
ENV FLASK_APP=server.py
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/')" || exit 1

# Run application with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --worker-class gthread --timeout 60 server:app
