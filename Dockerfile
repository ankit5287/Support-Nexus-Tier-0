# Use the official Python Alpine or Slim image to keep it lightweight!
FROM python:3.10-slim

# Set environment variables for production (no buffered output, no bytecode)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Install system dependencies required by typical ML libraries (like FAISS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code into the container
COPY . /app/

# Expose the standard Django port
EXPOSE 8000

# Set the default command to run the production server (in a real enterprise app, we'd use Gunicorn instead of runserver)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
