# Use a more specific base image for better caching
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY requirements.txt pyproject.toml* ./

# Install dependencies with pip
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# For ARM64 architecture, uncomment the following line and comment out the first FROM line
# FROM --platform=linux/arm64 python:3.11-slim as base

# CMD ["gunicorn", "-c", "gunicorn_config.py", "app.app:app"]
CMD ["python", "-m", "app.app"]
