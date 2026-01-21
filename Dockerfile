# Dockerfile

# Use official Python 3.12 slim image
FROM python:3.12.7-slim

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code to /app
COPY src ./src
COPY configs ./configs

# Check if data only has .gitkeep, if not, create empty data directory (no runtime data in image)
#COPY data ./data
RUN mkdir -p /app/data

# Default command: run HouseWatch
CMD ["python", "-m", "housewatch.main"]