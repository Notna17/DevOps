# Use slim Debian base for better compatibility with binary wheels and glibc.
FROM python:3.11-slim

# Install runtime dependencies (curl for healthcheck) and clean up apt cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the application.
WORKDIR /app

# Create a non-root user to run the service.
RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser

# Copy dependency manifest first to leverage build cache.
COPY requirements.txt /app/requirements.txt

# Install Python dependencies.
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code.
COPY . /app

# Drop privileges.
USER appuser

# Expose application port.
EXPOSE 8080

# Container healthcheck.
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl -f http://localhost:8080/health/alive || exit 1

# Run migrations, then start gunicorn.
ENTRYPOINT ["/bin/sh", "-c", "python migrate.py && exec gunicorn --bind 0.0.0.0:8080 app:app"]
