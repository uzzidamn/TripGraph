FROM python:3.11-slim

WORKDIR /app

# Install dependencies first — cached unless requirements.txt changes
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy full project source
COPY . /app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
