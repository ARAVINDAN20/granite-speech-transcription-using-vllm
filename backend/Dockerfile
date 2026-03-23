FROM vllm/vllm-openai:latest

# Install ffmpeg and audio processing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libsox-fmt-all \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Install Python audio libraries
RUN pip install --no-cache-dir \
    torchaudio \
    librosa \
    soundfile \
    pydub \
    webrtcvad
