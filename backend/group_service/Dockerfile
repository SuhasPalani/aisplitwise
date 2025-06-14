# Use a lightweight Python image as the base
FROM python:3.10-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache
# This means if requirements.txt doesn't change, pip install won't re-run
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# The 'app' directory inside your service folder (e.g., auth_service/app)
# will be copied to /app/app in the container
COPY ./app /app/app

# Expose the port that your FastAPI application will run on
# FastAPI's default Uvicorn port is 8000
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
# 'app.main:app' refers to the 'app' object in 'main.py' located inside the 'app' directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]