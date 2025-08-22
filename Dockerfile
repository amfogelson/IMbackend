# Use a stable Python version (NOT 3.13!)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies (no Cairo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Create directory for BCORE files
RUN mkdir -p /app/bcore_files

# Expose the port uvicorn will run on
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host=0.0.0.0", "--port=8000"]