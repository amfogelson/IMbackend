# Use a stable Python version (NOT 3.13!)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional, if needed for cairosvg or others)
RUN apt-get update && apt-get install -y \
    gcc \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port uvicorn will run on
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
