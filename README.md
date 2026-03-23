# 🎤 Granite Speech Transcription System

**Real-time speech-to-text transcription powered by IBM Granite 4.0 1B Speech model with GPU acceleration**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)](https://www.docker.com/)
[![GPU](https://img.shields.io/badge/GPU-NVIDIA%20CUDA-blue.svg)](https://developer.nvidia.com/cuda-zone)

---

## 🌟 Features

- ✅ **Live Microphone Transcription** - Real-time speech to text with audio visualization
- ✅ **File Upload Transcription** - Upload MP3, WAV, WebM, OGG, FLAC, M4A files
- ✅ **Multi-Format Support** - Automatic audio format conversion via ffmpeg
- ✅ **GPU Acceleration** - NVIDIA CUDA with vLLM for fast inference
- ✅ **Volume Boost** - 3x amplification for quiet audio
- ✅ **Audio Accumulation** - Buffers chunks for better accuracy
- ✅ **Speech Detection** - Validates audio contains speech before processing
- ✅ **Modern UI** - Responsive, beautiful interface with real-time feedback
- ✅ **CORS Enabled** - Browser-compatible API

---

## 🚀 Quick Start

### Prerequisites

- NVIDIA GPU with 8GB+ VRAM (RTX 3060/4060/5070 or better)
- NVIDIA Driver >= 525.60.13
- Docker >= 20.10
- Docker Compose >= 2.0
- NVIDIA Container Toolkit

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd ARS

# Configure Hugging Face token
echo "HF_TOKEN=your_hf_token_here" > .env

# Start all services
docker compose up -d

# Wait for model to load (2-3 minutes first time)
docker compose logs -f vllm-server

# Open in browser
# http://localhost:8080
```

### Verify Installation

```bash
# Check services
docker compose ps

# Test health endpoint
curl http://localhost:8080/health

# Expected: {"status":"healthy","proxy":"running",...}
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System architecture, data flow, component design |
| [PIPELINE.md](./docs/PIPELINE.md) | Complete request pipeline, step-by-step processing |
| [ERRORS.md](./docs/ERRORS.md) | All possible errors, causes, and solutions |
| [API.md](./docs/API.md) | Complete API reference with examples |
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Production deployment guide |
| [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Common issues and fixes |

---

## 🎯 Usage

### Live Microphone

1. Open http://localhost:8080
2. Click "🎙️ Start Recording"
3. Allow microphone access
4. Speak clearly for 5-10 seconds
5. Watch text appear in real-time
6. Click "⏹️ Stop Recording" when done

### File Upload

1. Scroll to "Upload Audio File" section
2. Click "📂 Choose File"
3. Select MP3, WAV, or other audio file (max 50MB)
4. Click "🚀 Transcribe"
5. Wait for processing (5-30 seconds)
6. Read transcription result

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Browser   │  Port 8080
│  (HTML/JS UI)   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│    Nginx        │  Port 8080
│  (Web Server)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│ Python  │ │  vLLM    │
│  Proxy  │ │  Server  │
│ Port    │ │  Port    │
│  8080   │ │  8000    │
│(internal)│ │(internal)│
└─────────┘ └──────────┘
     │            │
     │   WebM→WAV │ Granite Speech
     │   ffmpeg   │ Model (GPU)
     │   +3x gain │ BF16→FP16
     ▼            ▼
┌────────────────────────┐
│   NVIDIA GPU (RTX)     │
│   CUDA Acceleration    │
└────────────────────────┘
```

**See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed architecture documentation.**

---

## 🔧 Configuration

### Environment Variables

| Variable | File | Required | Description |
|----------|------|----------|-------------|
| `HF_TOKEN` | `.env` | Yes | Hugging Face API token |
| `VLLM_URL` | proxy | No | vLLM server URL (default: http://vllm:8000) |

### vLLM Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-model-len` | 512 | Maximum context length (tokens) |
| `--gpu-memory-utilization` | 0.6 | GPU VRAM usage (0.0-1.0) |
| `--enforce-eager` | True | Disable CUDA graphs (saves memory) |
| `--skip-mm-profiling` | True | Skip encoder profiling (prevents OOM) |
| `--dtype` | float16 | Model precision (float16/bfloat16) |

---

## 📊 Performance

### Benchmarks (RTX 5070 12GB)

| Metric | Value |
|--------|-------|
| Model Load Time | 2-3 minutes (first time) |
| VRAM Usage | 6-7 GB |
| Live Transcription Latency | 3-5 seconds per chunk |
| File Transcription (1 min) | 15-30 seconds |
| GPU Utilization | 50-80% during inference |
| Max Concurrent Requests | 1-2 |

### Supported Audio Formats

| Format | Extension | Live Mic | File Upload |
|--------|-----------|----------|-------------|
| WebM/Opus | .webm | ✅ Yes | ✅ Yes |
| WAV/PCM | .wav | ✅ Yes | ✅ Yes |
| MP3 | .mp3 | ❌ No | ✅ Yes |
| OGG | .ogg | ❌ No | ✅ Yes |
| FLAC | .flac | ❌ No | ✅ Yes |
| M4A | .m4a | ❌ No | ✅ Yes |

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Red status dot | vLLM not running | `docker compose restart vllm` |
| Microphone access denied | Browser blocked | Click 🔒 → Allow microphone |
| No speech detected | Audio too quiet | Speak louder, enable accumulation |
| Format not recognized | Corrupted file | Try WAV format |
| Upload fails | File > 50MB | Compress or split file |
| Slow response | Model loading | Wait 2-3 minutes |

**See [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) for complete troubleshooting guide.**

---

## 📁 Project Structure

```
ARS/
├── docker-compose.yml      # Docker orchestration
├── nginx.conf              # Nginx configuration
├── .env                    # Hugging Face token (SECRET)
├── .gitignore              # Git ignore rules
├── LICENSE                 # Apache 2.0 License
├── README.md               # This file
├── docs/
│   ├── ARCHITECTURE.md     # System architecture
│   ├── PIPELINE.md         # Request pipeline
│   ├── ERRORS.md           # Error reference
│   ├── API.md              # API documentation
│   ├── DEPLOYMENT.md       # Deployment guide
│   └── TROUBLESHOOTING.md  # Troubleshooting
├── backend/
│   └── Dockerfile          # vLLM with audio tools
├── proxy/
│   ├── Dockerfile          # Python proxy with ffmpeg
│   └── proxy.py            # Flask server (format conversion)
└── frontend/
    ├── index.html          # Main UI (live mic + file upload)
    └── test.html           # Diagnostic test page
```

---

## 🔒 Security

- **Protect HF Token** - Never commit `.env` to git
- **Local Access Only** - Services bind to localhost by default
- **Add Authentication** - Required for public deployments
- **Use HTTPS** - Required for microphone in production
- **Rate Limiting** - Recommended for public APIs

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

**Model License:** IBM Granite 4.0 1B Speech is licensed under Apache 2.0 by IBM.

---

## 🙏 Acknowledgments

- **IBM Granite** - For the excellent speech recognition model
- **vLLM Team** - For the high-performance inference engine
- **Hugging Face** - For the model hosting and transformers library
- **ffmpeg** - For audio format conversion

---

## 📞 Support

- **Documentation:** See `docs/` folder
- **Issues:** Open a GitHub issue
- **Discussions:** GitHub Discussions tab

---

## 🎯 Roadmap

- [ ] Add speaker diarization
- [ ] Support for streaming audio
- [ ] Multi-language UI
- [ ] WebSocket support for real-time streaming
- [ ] Batch file processing
- [ ] Export transcriptions (TXT, SRT, VTT)

---
