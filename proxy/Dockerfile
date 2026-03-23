FROM python:3.11-slim

# Install ffmpeg and audio tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    sox \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    requests \
    librosa \
    soundfile \
    numpy

COPY proxy.py .

EXPOSE 8080

CMD ["python", "proxy.py"]
