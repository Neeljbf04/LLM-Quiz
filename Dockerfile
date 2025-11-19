# ================================
#  Dockerfile for FastAPI + Playwright
# ================================
FROM python:3.10

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy project files
COPY . /app

# Environment vars (Render injects its own, but fallback)
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "start.sh"]
