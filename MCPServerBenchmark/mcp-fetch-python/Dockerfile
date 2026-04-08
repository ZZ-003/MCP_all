FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY fetch_server.py .

# Expose the port
EXPOSE 8000

# Run the MCP server
CMD ["python", "fetch_server.py"]