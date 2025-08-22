# Use a stable Python version (NOT 3.13!)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies with better error handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpango1.0-dev \
    libcairo2-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port uvicorn will run on
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host=0.0.0.0", "--port=8000"]