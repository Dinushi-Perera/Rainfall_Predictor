FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --default-timeout=120 --retries=10 -r requirements.txt

# Copy application code
COPY . .

EXPOSE 5000

# Run the app with Gunicorn so it listens on all container interfaces.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
