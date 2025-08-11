FROM python:3.12-alpine

# Install system dependencies including FFmpeg
RUN apk add --no-cache \
    ffmpeg \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create a non-root user for security
RUN useradd -m -u 1000 mediauser && chown -R mediauser:mediauser /app
USER mediauser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/browse')" || exit 1

# Run the application
CMD ["python", "app.py"]
