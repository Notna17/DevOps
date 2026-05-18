FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl -f http://localhost:8080/health/alive || exit 1

ENTRYPOINT ["/bin/sh", "-c", "python migrate.py && exec gunicorn --bind 0.0.0.0:8080 app:app"]
