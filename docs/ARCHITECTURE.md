# 🏗️ System Architecture

## Overview

The Granite Speech Transcription System is a distributed, containerized application that provides real-time speech-to-text transcription using IBM's Granite 4.0 1B Speech model with GPU acceleration.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client Layer                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Web Browser                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │
│  │  │ Live Mic UI  │  │ File Upload  │  │  Visualizer  │     │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS (Port 8080)
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      Nginx Server                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │
│  │  │ Static Files │  │  /v1/audio/  │  │    /v1/      │     │  │
│  │  │   (HTML)     │  │   → Proxy    │  │  → vLLM      │     │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│   Processing Layer      │      │    Inference Layer      │
│  ┌───────────────────┐  │      │  ┌───────────────────┐  │
│  │   Python Proxy    │  │      │  │    vLLM Server    │  │
│  │  (Flask + ffmpeg) │  │      │  │  (Granite Model)  │  │
│  │                   │  │      │  │                   │  │
│  │ • Format Convert  │  │      │  │ • Model Loading   │  │
│  │ • Volume Boost    │  │      │  │ • GPU Inference   │  │
│  │ • Speech Detect   │  │      │  │ • Token Generation│  │
│  │ • Chunk Accum     │  │      │  │                   │  │
│  └───────────────────┘  │      │  └───────────────────┘  │
└─────────────────────────┘      └─────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Hardware Acceleration Layer                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  NVIDIA GPU (CUDA)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │
│  │  │   VRAM 12GB  │  │  CUDA Cores  │  │ Tensor Cores │     │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Frontend (Browser)

**Technology:** Vanilla HTML5, CSS3, JavaScript (ES6+)

**Components:**
```
┌─────────────────────────────────────────┐
│           Frontend Application           │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │        Status Bar Component        │  │
│  │  • Server connection indicator    │  │
│  │  • Model name display             │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │    Live Microphone Component       │  │
│  │  • MediaRecorder API              │  │
│  │  • Audio visualization (Web Audio)│  │
│  │  • Chunk-based streaming          │  │
│  │  • Real-time transcription display│  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │     File Upload Component          │  │
│  │  • File input (multiple formats)  │  │
│  │  • Progress indicator             │  │
│  │  • Result display                 │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Data Flow:**
1. User clicks "Start Recording"
2. Browser requests microphone access (getUserMedia API)
3. MediaRecorder captures audio as WebM/Opus blobs
4. Chunks sent every 1 second via FormData to Nginx
5. Response received, transcription displayed
6. Audio visualization updated via Web Audio API

---

### 2. Nginx (API Gateway)

**Technology:** Nginx Alpine

**Responsibilities:**
- Serve static files (HTML, CSS, JS)
- Route API requests to appropriate backend
- Handle CORS preflight requests
- Manage request timeouts
- Enforce file size limits (50MB max)

**Routing Configuration:**
```
Request Path          →  Destination
─────────────────────────────────────────────
/                     →  /usr/share/nginx/html (static files)
/v1/audio/*           →  http://proxy:8080/v1/audio/ (Python Proxy)
/v1/*                 →  http://vllm:8000/v1/ (vLLM Server)
/health               →  http://proxy:8080/health (Health Check)
```

**CORS Handling:**
```nginx
# All origins allowed (for development)
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type

# Preflight handling
OPTIONS requests → 204 No Content
```

---

### 3. Python Proxy (Audio Processing)

**Technology:** Flask + ffmpeg + librosa

**Responsibilities:**
- Convert any audio format to WAV/PCM
- Apply volume boost (3x gain)
- Analyze audio for speech presence
- Accumulate audio chunks
- Forward to vLLM for transcription

**Processing Pipeline:**
```
┌─────────────────────────────────────────────────────────────┐
│                  Python Proxy Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Receive Audio (WebM/MP3/WAV/etc.)                       │
│         │                                                    │
│         ▼                                                    │
│  2. Validate Input                                          │
│         │                                                    │
│         ▼                                                    │
│  3. Convert to WAV (ffmpeg)                                 │
│     • Sample rate: 16000 Hz                                 │
│     • Channels: 1 (mono)                                    │
│     • Codec: PCM 16-bit                                     │
│     • Volume: +3.0 dB gain                                  │
│         │                                                    │
│         ▼                                                    │
│  4. Analyze Audio (librosa)                                 │
│     • RMS energy                                            │
│     • Silence ratio                                         │
│     • Duration                                              │
│     • Speech detection heuristic                            │
│         │                                                    │
│         ▼                                                    │
│  5. Accumulate Chunks (if enabled)                          │
│     • Buffer until ~96KB (~3 seconds)                       │
│     • Combine chunks                                        │
│         │                                                    │
│         ▼                                                    │
│  6. Send to vLLM                                            │
│     • POST /v1/audio/transcriptions                         │
│     • WAV file via multipart/form-data                      │
│         │                                                    │
│         ▼                                                    │
│  7. Return Response                                         │
│     • Transcription text                                    │
│     • Debug info                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Audio Format Conversion:**
```python
# ffmpeg command structure
ffmpeg -y \
  -i input.any_format \
  -ar 16000 \           # 16kHz sample rate
  -ac 1 \               # Mono channel
  -c:a pcm_s16le \      # PCM 16-bit little-endian
  -af volume=3.0 \      # 3x volume boost
  output.wav
```

**Speech Detection Heuristic:**
```python
has_speech = (
    duration >= 1.0 and      # At least 1 second
    rms_energy > 0.01 and    # Minimum energy level
    silence_ratio < 0.9 and  # Less than 90% silence
    max_amplitude > 0.05     # Minimum peak amplitude
)
```

---

### 4. vLLM Server (Model Inference)

**Technology:** vLLM + PyTorch + CUDA

**Responsibilities:**
- Load IBM Granite Speech model
- Manage GPU memory
- Process audio transcription requests
- Generate text output

**Model Architecture:**
```
IBM Granite 4.0 1B Speech
├── Speech Encoder (Conformer)
│   • 16 layers
│   • 1024 hidden dimension
│   • 8 attention heads
│   • CTC-based alignment
│
├── Speech Projector (Q-Former)
│   • 2-layer transformer
│   • Temporal downsampling (10x)
│   • Modality alignment
│
└── LLM Backbone (Granite 1B)
    • Transformer decoder
    • 128K context support
    • BF16 precision
```

**Memory Management:**
```
GPU VRAM Allocation (12GB total):
├── Model Weights: ~4.3 GB (BF16)
├── KV Cache: ~1.6 GB (configurable)
├── Activations: ~2-3 GB (during inference)
└── Reserved: ~3 GB (for safety margin)
```

**Optimization Flags:**
```bash
--max-model-len 512          # Limit context length
--gpu-memory-utilization 0.6 # Use 60% of VRAM
--enforce-eager              # Disable CUDA graphs
--skip-mm-profiling          # Skip encoder profiling
--dtype float16              # Use FP16 precision
```

---

## Data Flow

### Live Microphone Flow

```
User speaks
    │
    ▼
Browser MediaRecorder API
    │
    ▼ (WebM/Opus blob, 1-second chunks)
FormData POST to /v1/audio/transcriptions
    │
    ▼
Nginx (Port 8080)
    │
    ▼ (proxy_pass)
Python Proxy (Port 8080 internal)
    │
    ▼ (ffmpeg conversion)
WebM/Opus → WAV/PCM (16kHz, mono, 16-bit)
    │
    ▼ (volume boost +3dB)
Audio analysis (librosa)
    │
    ▼ (speech detection)
Accumulate chunks (if enabled)
    │
    ▼ (when buffer >= 96KB)
POST to vLLM /v1/audio/transcriptions
    │
    ▼
vLLM Server
    │
    ▼ (Granite Speech model)
Audio → Text transcription
    │
    ▼
JSON response: {"text": "...", "_debug": {...}}
    │
    ▼
Nginx
    │
    ▼
Browser JavaScript
    │
    ▼
Update UI with transcription
```

### File Upload Flow

```
User selects file (MP3/WAV/etc.)
    │
    ▼
Browser File Input
    │
    ▼ (multipart/form-data)
FormData POST to /v1/audio/transcriptions
    │
    ▼
Nginx (Port 8080)
    │
    ▼ (proxy_pass, max 50MB)
Python Proxy (Port 8080 internal)
    │
    ▼ (ffmpeg conversion)
Any format → WAV/PCM
    │
    ▼ (volume boost +3dB)
Audio analysis (librosa)
    │
    ▼ (no accumulation for files)
POST to vLLM /v1/audio/transcriptions
    │
    ▼
vLLM Server
    │
    ▼ (Granite Speech model)
Audio → Text transcription
    │
    ▼
JSON response
    │
    ▼
Nginx
    │
    ▼
Browser JavaScript
    │
    ▼
Display transcription result
```

---

## Network Architecture

### Docker Networking

```
┌────────────────────────────────────────────────┐
│            Docker Bridge Network               │
│              (app-network)                      │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐           │
│  │  vllm-server │  │ audio-proxy  │           │
│  │  172.19.0.2  │  │ 172.19.0.3   │           │
│  │  Port 8000   │  │ Port 8080    │           │
│  └──────────────┘  └──────────────┘           │
│         │                  │                   │
│         └────────┬─────────┘                   │
│                  │                             │
│         ┌────────▼────────┐                    │
│         │transcription-   │                    │
│         │    nginx        │                    │
│         │  172.19.0.4     │                    │
│         │  Port 80        │                    │
│         └────────┬────────┘                    │
└──────────────────│────────────────────────────┘
                   │
                   │ Port Mapping
                   │ 0.0.0.0:8080 → 80
                   ▼
            Host Machine
            (localhost:8080)
```

### Port Configuration

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| vLLM Server | 8000 | Not exposed | Model inference API |
| Python Proxy | 8080 | Not exposed | Audio processing |
| Nginx | 80 | 8080 | Web server + API gateway |

---

## Security Architecture

### Network Isolation

```
Internet
    │
    ▼
┌─────────────────────────┐
│   Host Firewall         │
│   (iptables/ufw)        │
└─────────────────────────┘
    │
    ▼ (Port 8080 only)
┌─────────────────────────┐
│   Docker Network        │
│   (Bridge isolation)    │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│   Container Network     │
│   (Internal only)       │
└─────────────────────────┘
```

### Data Protection

- **HF Token:** Stored in `.env` file (gitignored)
- **No Data Persistence:** Audio processed in-memory, not stored
- **Temporary Files:** Deleted immediately after processing
- **CORS:** Configured for localhost (development)

---

## Scalability Considerations

### Current Limitations

1. **Single GPU:** One vLLM instance per GPU
2. **No Load Balancing:** Single point of failure
3. **No Queue:** Requests processed synchronously
4. **Memory Constraints:** Limited by GPU VRAM

### Scaling Options

**Horizontal Scaling:**
```
Load Balancer (HAProxy/Traefik)
    │
    ├──→ Instance 1 (GPU 1)
    ├──→ Instance 2 (GPU 2)
    └──→ Instance N (GPU N)
```

**Vertical Scaling:**
- Increase GPU VRAM (24GB/48GB GPUs)
- Increase `--gpu-memory-utilization`
- Increase `--max-model-len`

**Async Processing:**
```
Request → Message Queue (Redis/RabbitMQ)
    │
    ▼
Worker Pool (Multiple vLLM instances)
    │
    ▼
Result Storage (Database/Cache)
```

---

## Monitoring Points

### Key Metrics

1. **GPU Utilization:** `nvidia-smi --query-gpu=utilization.gpu`
2. **VRAM Usage:** `nvidia-smi --query-gpu=memory.used`
3. **Request Latency:** Proxy processing time
4. **Error Rate:** Failed transcriptions / Total requests
5. **Queue Depth:** Number of pending requests

### Health Checks

```bash
# Service health
curl http://localhost:8080/health

# Model availability
curl http://localhost:8080/v1/models

# GPU status
nvidia-smi

# Container status
docker compose ps
```

---

## Failure Modes

### Component Failures

| Component | Failure Mode | Impact | Recovery |
|-----------|-------------|--------|----------|
| vLLM Server | OOM crash | No transcription | Auto-restart |
| Python Proxy | ffmpeg error | No conversion | Error response |
| Nginx | Port conflict | No access | Manual fix |
| Frontend | CORS error | No UI | Browser cache clear |
| GPU | Driver crash | System down | Driver reload |

### Graceful Degradation

- **High Load:** Queue requests, return 429 Too Many Requests
- **Low VRAM:** Reduce batch size, limit concurrent requests
- **Format Error:** Return clear error message with supported formats
- **No Speech:** Return empty text with audio analysis info

---

**This architecture document provides a complete overview of the system design, component interactions, and operational considerations.**
