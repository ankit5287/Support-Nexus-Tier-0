# Logic Stream: AI Specialist Tier Dockerfile
# Optimized for Hugging Face Spaces (CPU Basic)

FROM python:3.9-slim

# Set environment variables for quality and stability
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

WORKDIR /app

# Install system-level build dependencies for ML/Analytics
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install heavy ML stack first to leverage Docker layer caching
COPY requirements_docker.txt .
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copy the architectural core and the fine-tuned BERT model weights
COPY . .

# Ensure the database exists (using the included db.sqlite3)
# Note: Data in Hugging Face /app is ephemeral unless a persistent volume is mounted
RUN python manage.py migrate --noinput

# Perform Enterprise Static Asset Collection
RUN python manage.py collectstatic --noinput

# Create a non-root user for high-end security compliance
RUN useradd -m logic_user && chown -R logic_user:logic_user /app
USER logic_user

# EXPOSE the mandatory Hugging Face port
EXPOSE 7860

# Launch the Command Center via Gunicorn
# Bind to 0.0.0.0:7860 as required by Hugging Face Spaces
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "devsupport_nexus.wsgi:application"]
