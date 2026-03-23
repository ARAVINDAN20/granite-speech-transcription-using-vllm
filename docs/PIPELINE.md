# 🔄 Complete Request Pipeline

## Overview

This document details the complete end-to-end pipeline for audio transcription requests, from browser capture to final transcription display.

---

## Pipeline Stages

```
┌──────────────────────────────────────────────────────────────────┐
│                    Complete Transcription Pipeline                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Stage 1: Audio Capture (Browser)                                │
│         │                                                         │
│         ▼                                                         │
│  Stage 2: HTTP Transmission                                      │
│         │                                                         │
│         ▼                                                         │
│  Stage 3: Nginx Routing                                          │
│         │                                                         │
│         ▼                                                         │
│  Stage 4: Format Conversion (Python Proxy)                       │
│         │                                                         │
│         ▼                                                         │
│  Stage 5: Audio Analysis                                         │
│         │                                                         │
│         ▼                                                         │
│  Stage 6: Chunk Accumulation (Optional)                          │
│         │                                                         │
│         ▼                                                         │
│  Stage 7: vLLM Inference                                         │
│         │                                                         │
│         ▼                                                         │
│  Stage 8: Response Processing                                    │
│         │                                                         │
│         ▼                                                         │
│  Stage 9: UI Display                                             │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Audio Capture (Browser)

### Live Microphone Capture

**Technology:** MediaRecorder API (Web Audio API)

**Process:**
```javascript
// 1. Request microphone access
const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000
    }
});

// 2. Initialize MediaRecorder
const mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'audio/webm;codecs=opus'
});

// 3. Start recording (request data every 1 second)
mediaRecorder.start(1000);

// 4. Collect chunks
mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
        audioChunks.push(event.data);
    }
};
```

**Audio Format:**
- **Container:** WebM
- **Codec:** Opus
- **Sample Rate:** 16000 Hz (requested)
- **Channels:** 1 (mono)
- **Bit Rate:** 128 kbps
- **Chunk Duration:** 1 second
- **Chunk Size:** ~16 KB per second

### File Upload Capture

**Technology:** HTML5 File Input API

**Process:**
```html
<input type="file" id="audioFile" accept="audio/*,.wav,.mp3,.webm,.ogg,.flac,.m4a">
```

```javascript
// 1. User selects file
const file = document.getElementById('audioFile').files[0];

// 2. Validate
if (file.size > 50 * 1024 * 1024) {
    throw new Error('File too large (max 50MB)');
}

// 3. Prepare FormData
const formData = new FormData();
formData.append('file', file, file.name);
formData.append('model', 'ibm-granite/granite-4.0-1b-speech');
```

**Supported Formats:**
- WebM/Opus
- WAV/PCM
- MP3/MPEG
- OGG/Vorbis
- FLAC
- M4A/AAC

---

## Stage 2: HTTP Transmission

### Request Construction

**Method:** POST  
**URL:** `/v1/audio/transcriptions`  
**Content-Type:** `multipart/form-data`

**Request Structure:**
```http
POST /v1/audio/transcriptions HTTP/1.1
Host: localhost:8080
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: <calculated>

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="audio.webm"
Content-Type: audio/webm

[binary audio data]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="model"

ibm-granite/granite-4.0-1b-speech
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="accumulate"

true
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="session_id"

session-abc123
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | Binary | Yes | Audio file (WebM, MP3, WAV, etc.) |
| `model` | String | No | Model name (default: ibm-granite/granite-4.0-1b-speech) |
| `accumulate` | Boolean | No | Buffer chunks (default: true) |
| `session_id` | String | No | Session identifier for accumulation |

---

## Stage 3: Nginx Routing

### Request Handling

**Configuration:**
```nginx
location /v1/audio/ {
    proxy_pass http://proxy:8080/v1/audio/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    # CORS
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Content-Type' always;
    
    # Timeouts
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;
    
    # Max file size
    client_max_body_size 50M;
}
```

### Routing Logic

```
Request: POST /v1/audio/transcriptions
    │
    ▼
┌─────────────────────────────────┐
│  Nginx Location Matching        │
│  location /v1/audio/ { ... }    │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Proxy Pass to Python Proxy     │
│  proxy_pass http://proxy:8080   │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Headers Forwarded              │
│  • Host                         │
│  • X-Real-IP                    │
│  • X-Forwarded-For              │
└─────────────────────────────────┘
```

### CORS Handling

**Preflight Request (OPTIONS):**
```http
OPTIONS /v1/audio/transcriptions HTTP/1.1
Origin: http://localhost:8080
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Actual Request:**
```http
POST /v1/audio/transcriptions HTTP/1.1
Origin: http://localhost:8080

HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
```

---

## Stage 4: Format Conversion (Python Proxy)

### Input Validation

```python
@app.route('/v1/audio/transcriptions', methods=['POST'])
def transcribe():
    # 1. Check for file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # 2. Read audio bytes
    audio_bytes = file.read()
    file_size = len(audio_bytes)
    filename = file.filename or 'audio'
    
    # 3. Log input
    print(f"📥 Received: {filename}, {file_size} bytes, type: {file.content_type}")
```

### Format Conversion (ffmpeg)

**Purpose:** Convert any audio format to WAV/PCM (required by Granite Speech model)

**Process:**
```python
def convert_audio_to_wav(audio_bytes: bytes) -> bytes:
    # 1. Create temp files
    with tempfile.NamedTemporaryFile(suffix='.input', delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
        tmp_out_path = tmp_out.name
    
    try:
        # 2. Build ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-i', tmp_in_path,
            '-ar', '16000',        # 16kHz sample rate
            '-ac', '1',            # Mono channel
            '-c:a', 'pcm_s16le',   # PCM 16-bit little-endian
            '-af', 'volume=3.0',   # 3x volume boost
            tmp_out_path
        ]
        
        # 3. Execute ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:200]}")
        
        # 4. Read converted WAV
        with open(tmp_out_path, 'rb') as f:
            wav_bytes = f.read()
        
        # 5. Validate output
        if len(wav_bytes) < 1000:
            raise RuntimeError("Converted WAV too small")
        
        return wav_bytes
        
    finally:
        # 6. Cleanup temp files
        for path in [tmp_in_path, tmp_out_path]:
            if os.path.exists(path):
                os.unlink(path)
```

**Output Format:**
- **Container:** WAV (RIFF)
- **Codec:** PCM (Pulse Code Modulation)
- **Sample Rate:** 16000 Hz
- **Bit Depth:** 16-bit
- **Channels:** 1 (mono)
- **Byte Rate:** 32000 bytes/sec
- **Block Align:** 2 bytes
- **Volume Boost:** +3.0 dB (3x amplitude)

### Volume Boost Rationale

**Why 3x boost?**
- Browser recordings often quiet
- Improves speech detection accuracy
- Compensates for distance from mic
- Prevents "no speech detected" errors

**Implementation:**
```python
'-af', 'volume=3.0'  # ffmpeg audio filter
```

---

## Stage 5: Audio Analysis

### Speech Detection

**Technology:** librosa (audio analysis library)

**Process:**
```python
def analyze_audio(wav_bytes: bytes) -> dict:
    import librosa
    
    # 1. Load audio
    y, sr = librosa.load(io.BytesIO(wav_bytes), sr=16000, mono=True)
    
    # 2. Calculate metrics
    duration = len(y) / sr
    rms = float(librosa.feature.rms(y=y)[0].mean())  # Root Mean Square energy
    silence_ratio = float((abs(y) < 0.01).mean())    # % of near-silence samples
    max_amp = float(abs(y).max())                     # Peak amplitude
    
    # 3. Speech detection heuristic
    has_speech = (
        duration >= 1.0 and      # At least 1 second
        rms > 0.01 and           # Minimum energy level
        silence_ratio < 0.9 and  # Less than 90% silence
        max_amp > 0.05           # Minimum peak amplitude
    )
    
    return {
        'valid': True,
        'duration_sec': round(duration, 2),
        'sample_rate': sr,
        'samples': len(y),
        'rms_energy': round(rms, 4),
        'silence_ratio': round(silence_ratio, 2),
        'peak_amplitude': round(max_amp, 4),
        'has_speech': has_speech
    }
```

**Metrics Explained:**

| Metric | Description | Threshold | Purpose |
|--------|-------------|-----------|---------|
| `duration_sec` | Audio length in seconds | >= 1.0 | Too short = unreliable |
| `rms_energy` | Average signal energy | > 0.01 | Detects presence of sound |
| `silence_ratio` | % of silent samples | < 0.9 | Filters out mostly-silent audio |
| `peak_amplitude` | Maximum amplitude | > 0.05 | Ensures sufficient volume |

**Example Analysis:**
```json
{
  "valid": true,
  "duration_sec": 3.5,
  "sample_rate": 16000,
  "samples": 56000,
  "rms_energy": 0.0523,
  "silence_ratio": 0.32,
  "peak_amplitude": 0.847,
  "has_speech": true
}
```

---

## Stage 6: Chunk Accumulation (Optional)

### Purpose

- Buffer multiple short chunks
- Improve transcription accuracy
- Reduce API calls to vLLM
- Handle very short utterances

### Process

```python
# 1. Check if accumulation enabled
accumulate = request.form.get('accumulate', 'true').lower() == 'true'

if accumulate:
    # 2. Add to session buffer
    audio_buffers[session_id].append(wav_bytes)
    total_size = sum(len(b) for b in audio_buffers[session_id])
    
    # 3. Check if enough audio collected (~96KB = ~3 seconds)
    if total_size < 96000:
        return jsonify({
            'text': '',
            'status': 'accumulating',
            'buffered_bytes': total_size,
            'required_bytes': 96000,
            'audio_info': audio_info
        }), 200
    
    # 4. Combine all buffered chunks
    combined = b''.join(audio_buffers[session_id])
    audio_buffers[session_id] = []  # Clear buffer
    wav_bytes = combined
    
    print(f"🔗 Accumulated: {len(wav_bytes)} bytes")
```

**Accumulation Threshold:**
- **Minimum:** 96000 bytes (~3 seconds at 16kHz, 16-bit, mono)
- **Typical:** 2-5 chunks (2-5 seconds)
- **Maximum:** No limit (cleared after sending)

**Session Management:**
- Each session has unique `session_id`
- Sessions persist in memory
- Buffers cleared after sending to vLLM
- No expiration (manual cleanup needed for long-running servers)

---

## Stage 7: vLLM Inference

### Request to vLLM

```python
# 1. Prepare request
vllm_response = requests.post(
    f'{VLLM_URL}/v1/audio/transcriptions',
    files={'file': ('audio.wav', io.BytesIO(wav_bytes), 'audio/wav')},
    data={'model': model},
    timeout=90
)

# 2. Handle response
if vllm_response.status_code != 200:
    return jsonify({
        'error': 'vLLM error',
        'status': vllm_response.status_code,
        'response': vllm_response.text[:200]
    }), vllm_response.status_code

result = vllm_response.json()
```

### vLLM Processing (Internal)

**Inside vLLM Server:**

```
1. Receive WAV file
   │
   ▼
2. Parse WAV header
   • Sample rate: 16000 Hz
   • Channels: 1
   • Bit depth: 16
   │
   ▼
3. Extract audio features
   • Log-Mel spectrogram
   • 80 Mel bins
   • 25ms windows, 10ms hop
   │
   ▼
4. Speech Encoder (Conformer)
   • 16 layers
   • Self-attention + CNN
   • CTC alignment
   │
   ▼
5. Speech Projector (Q-Former)
   • 2-layer transformer
   • 10x temporal downsampling
   • Modality alignment
   │
   ▼
6. LLM Backbone (Granite 1B)
   • Transformer decoder
   • Autoregressive generation
   • Max 512 tokens
   │
   ▼
7. Generate transcription
   • Token-by-token generation
   • Beam search (beam=1)
   • Max 200 tokens
   │
   ▼
8. Return result
   {"text": "hello this is a test"}
```

**Model Parameters:**
- **Input:** 16kHz mono WAV
- **Feature Extraction:** 80-dim log-Mel spectrogram
- **Encoder:** 16-layer Conformer (1024 dim, 8 heads)
- **Projector:** 2-layer Q-Former (3 queries per block)
- **LLM:** Granite 1B (transformer decoder)
- **Output:** Text transcription (UTF-8)

**Inference Time:**
- **Feature Extraction:** ~50ms
- **Encoder:** ~200ms
- **Projector:** ~50ms
- **LLM Decoding:** ~100ms per token
- **Total (3s audio):** ~2-5 seconds

---

## Stage 8: Response Processing

### Response Structure

```python
result = vllm_response.json()

# Add debug information
result['_debug'] = {
    'audio_info': audio_info,
    'processing_time_sec': round(elapsed, 2),
    'input_bytes': len(wav_bytes),
    'accumulated': accumulate
}

return jsonify(result)
```

**Complete Response:**
```json
{
  "text": "hello this is a test transcription",
  "_debug": {
    "audio_info": {
      "duration_sec": 3.5,
      "sample_rate": 16000,
      "samples": 56000,
      "rms_energy": 0.0523,
      "silence_ratio": 0.32,
      "peak_amplitude": 0.847,
      "has_speech": true
    },
    "processing_time_sec": 5.23,
    "input_bytes": 112000,
    "accumulated": true
  }
}
```

### Response Handling (Nginx)

```nginx
# Nginx forwards response back to browser
proxy_pass http://proxy:8080/v1/audio/;
proxy_http_version 1.1;
proxy_set_header Host $host;

# CORS headers added
add_header Access-Control-Allow-Origin * always;
```

---

## Stage 9: UI Display

### Browser Response Handling

```javascript
async function transcribeChunk(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    formData.append('model', 'ibm-granite/granite-4.0-1b-speech');
    formData.append('accumulate', 'true');
    
    const response = await fetch('/v1/audio/transcriptions', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    
    // Handle different response types
    if (data.text && data.text.trim()) {
        // Got transcription!
        fullTranscript = data.text.trim();
        
        const transcriptEl = document.getElementById('transcript');
        transcriptEl.textContent = fullTranscript;
        transcriptEl.classList.add('new-text');
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
            transcriptEl.classList.remove('new-text');
        }, 3000);
        
        showStatus(`✅ "${data.text.trim()}"`, 'alert-success');
        
    } else if (data.status === 'accumulating') {
        // Still buffering
        const pct = Math.round((data.buffered_bytes / data.required_bytes) * 100);
        showStatus(`⏳ Buffering audio... ${pct}%`, 'alert-info');
        
    } else if (data.status === 'no_speech') {
        // No speech detected
        showStatus('⚠️ No speech detected - speak louder!', 'alert-warning');
    }
}
```

### UI Updates

**Transcription Display:**
```html
<div class="output">
    <div class="output-label">📝 Live Transcription:</div>
    <div class="output-text new-text">
        hello this is a test transcription
    </div>
    <div class="debug-info">
        ✓ 3.5s audio | Energy: 0.0523 | 5.23s
    </div>
</div>
```

**Status Messages:**
```javascript
function showStatus(message, className) {
    const area = document.getElementById('statusArea');
    area.innerHTML = `<div class="alert ${className}">${message}</div>`;
}
```

**Visual Feedback:**
- ✅ Green alert for success
- ⚠️ Yellow alert for warnings
- ❌ Red alert for errors
- ⏳ Blue alert for info/progress

---

## Complete Pipeline Timing

### End-to-End Latency Breakdown

| Stage | Time (ms) | Description |
|-------|-----------|-------------|
| Audio Capture | 1000 | 1-second chunk recording |
| HTTP Transmission | 10-50 | Browser → Nginx |
| Nginx Routing | 1-5 | Proxy pass |
| Format Conversion | 500-2000 | ffmpeg WebM→WAV |
| Audio Analysis | 100-300 | librosa analysis |
| Accumulation | 0-3000 | Waiting for buffer |
| vLLM Inference | 2000-5000 | Model processing |
| Response Return | 10-50 | vLLM → Browser |
| UI Update | 10-50 | DOM manipulation |
| **Total** | **3631-11455** | **~4-11 seconds** |

### Optimization Opportunities

1. **Reduce Chunk Size:** Smaller chunks = faster response (but less accurate)
2. **Parallel Processing:** Analyze while converting
3. **Streaming:** Start inference before full chunk received
4. **GPU Optimization:** Increase batch size
5. **Cache:** Reuse model weights across requests

---

## Error Handling Pipeline

### Error Propagation

```
Error Source          →  Error Handler          →  User Message
─────────────────────────────────────────────────────────────────────
Microphone denied     →  Browser JS             →  "Allow mic access"
Network error         →  fetch() catch          →  "Connection failed"
File too large        →  Nginx (50MB limit)     →  "413 Payload Too Large"
Format conversion     →  Python Proxy           →  "Audio conversion failed"
No speech detected    →  analyze_audio()        →  "No speech detected"
vLLM error            →  Python Proxy           →  "Server error"
Timeout               →  requests.post(90s)     →  "Request timed out"
```

### Retry Logic

```javascript
// Browser-side retry (for transient errors)
async function transcribeWithRetry(audioBlob, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await transcribeChunk(audioBlob);
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
}
```

---

**This pipeline document provides complete visibility into how audio flows through the system, from capture to transcription display.**
