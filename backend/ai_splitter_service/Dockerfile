# backend/reporting_service/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

ENV PYTHONPATH=/app

# No EXPOSE 8000 needed for background worker

# Corrected CMD for background worker
CMD ["python", "app/main.py"]