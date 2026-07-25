FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "flask>=3.0" "requests>=2.31" "gunicorn>=21.2"

WORKDIR /app
COPY app.py /app/app.py

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4"]
