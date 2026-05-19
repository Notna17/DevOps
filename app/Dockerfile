# Base image with glibc for broader wheel compatibility.
FROM python:3.11-slim

# Install curl for healthcheck and clean apt cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory.
WORKDIR /app

# Create a non-root user for runtime.
RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser

# Copy dependency manifest first to leverage cache.
COPY requirements.txt /app/requirements.txt

# Install Python dependencies.
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source.
COPY . /app

# Drop privileges.
USER appuser

# Expose the app port.
EXPOSE 8080

# Healthcheck for liveness endpoint.
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl -f http://localhost:8080/health/alive || exit 1

# Run migrations then start gunicorn.
ENTRYPOINT ["/bin/sh", "-c", "python migrate.py && exec gunicorn --bind 0.0.0.0:8080 app:app"]
