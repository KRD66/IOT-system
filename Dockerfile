FROM python:3.13-slim

# Install system dependencies for PyAudio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn voiceweb.wsgi:application --bind 0.0.0.0:$PORT --workers 2"]