FROM python:3.11-slim

# Update packages and install required tools
RUN apt-get update && apt-get install -y \
    pandoc \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Expose port 8000
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]
