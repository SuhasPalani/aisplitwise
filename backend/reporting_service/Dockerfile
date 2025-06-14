# backend/reporting_service/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

ENV PYTHONPATH=/app

# REMOVE THIS LINE: EXPOSE 8000

# CHANGE THIS CMD LINE:
# Old: CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# New: Directly execute the Python script
CMD ["python", "app/main.py"]