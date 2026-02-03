FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 jobsearch && chown -R jobsearch:jobsearch /app
USER jobsearch

# Run migrations and start app
CMD gunicorn --bind 0.0.0.0:$PORT wsgi:app --workers=4 --threads=2 --timeout=120