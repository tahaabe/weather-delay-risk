FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . .

# Expose port 8000
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "serving.main:app", "--host", "0.0.0.0", "--port", "8000"]