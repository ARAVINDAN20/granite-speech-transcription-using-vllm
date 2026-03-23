# ❌ Error Reference Guide

## Overview

This document provides a comprehensive reference for all errors that may occur in the Granite Speech Transcription System, including causes, solutions, and prevention strategies.

---

## Error Categories

1. [Client-Side Errors (Browser)](#client-side-errors)
2. [Network Errors](#network-errors)
3. [Nginx Errors](#nginx-errors)
4. [Python Proxy Errors](#python-proxy-errors)
5. [vLLM Server Errors](#vllm-server-errors)
6. [GPU/Hardware Errors](#gpuhardware-errors)
7. [Model Errors](#model-errors)

---

## Client-Side Errors

### 1. Microphone Access Denied

**Error Message:**
```
NotAllowedError: Permission denied
```

**Browser Console:**
```
Microphone error: NotAllowedError: Permission denied
```

**Cause:**
- User clicked "Block" on microphone permission popup
- Browser settings block microphone access
- OS-level microphone privacy settings disabled

**Solution:**
```javascript
// Check error type
if (error.name === 'NotAllowedError') {
    showStatus('❌ Microphone access denied. Click the 🔒 icon in address bar and allow microphone.', 'alert-error');
}
```

**User Fix:**
1. Click 🔒 lock icon in browser address bar
2. Find "Microphone" setting
3. Toggle to "Allow"
4. Refresh page (F5)

**Prevention:**
- Show clear instructions before requesting mic access
- Explain why microphone is needed
- Provide alternative (file upload) if mic unavailable

---

### 2. No Microphone Found

**Error Message:**
```
NotFoundError: No media devices found
```

**Cause:**
- No microphone connected
- Microphone disabled in OS settings
- Browser cannot access audio devices

**Solution:**
```javascript
if (error.name === 'NotFoundError') {
    showStatus('❌ No microphone found. Connect a microphone and try again.', 'alert-error');
}
```

**User Fix:**
1. Check microphone is connected
2. Open OS sound settings
3. Ensure microphone is not disabled
4. Try different browser

---

### 3. MediaRecorder Not Supported

**Error Message:**
```
TypeError: MediaRecorder is not defined
```

**Cause:**
- Old browser (IE, old Safari)
- Browser doesn't support MediaRecorder API

**Solution:**
```javascript
if (!window.MediaRecorder) {
    showStatus('❌ Browser not supported. Please use Chrome, Firefox, or Edge.', 'alert-error');
}
```

**User Fix:**
- Use modern browser (Chrome 90+, Firefox 88+, Edge 90+)

---

### 4. File Too Large

**Error Message:**
```
File size exceeds 50MB limit
```

**Cause:**
- User selected file larger than 50MB

**Solution:**
```javascript
if (selectedFile.size > 50 * 1024 * 1024) {
    showUploadStatus('❌ File too large. Maximum size is 50MB.', 'alert-error');
    return;
}
```

**User Fix:**
- Compress audio file
- Use shorter audio clip
- Convert to more efficient format (OGG, MP3)

---

## Network Errors

### 1. Connection Refused

**Error Message:**
```
TypeError: Failed to fetch
NetworkError: Connection refused
```

**Cause:**
- Services not running
- Wrong port
- Firewall blocking connection

**Solution:**
```javascript
try {
    const response = await fetch('/v1/audio/transcriptions', {...});
} catch (error) {
    showStatus('❌ Cannot connect to server. Make sure services are running.', 'alert-error');
    console.error('Connection error:', error);
}
```

**User Fix:**
```bash
# Check services
docker compose ps

# Restart if needed
docker compose restart
```

---

### 2. Request Timeout

**Error Message:**
```
AbortError: The operation was aborted
TimeoutError: Request timed out
```

**Cause:**
- Server taking too long (>60s default)
- Network latency
- Server overloaded

**Solution:**
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

const response = await fetch('/v1/audio/transcriptions', {
    method: 'POST',
    body: formData,
    signal: controller.signal
});
```

**User Fix:**
- Wait longer (first request may be slow)
- Check server logs: `docker compose logs vllm-server`
- Reduce audio length

---

### 3. CORS Error

**Error Message:**
```
Access to fetch at 'http://localhost:8080/v1/audio/transcriptions' from origin 'null' has been blocked by CORS policy
```

**Cause:**
- Opening HTML file directly (file:// protocol)
- Nginx CORS configuration missing
- Wrong origin in CORS headers

**Solution (Nginx):**
```nginx
location /v1/audio/ {
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Content-Type' always;
    
    if ($request_method = 'OPTIONS') {
        return 204;
    }
}
```

**User Fix:**
- Use http://localhost:8080 (not file://)
- Serve via HTTP server

---

## Nginx Errors

### 1. 413 Payload Too Large

**HTTP Status:** 413

**Error Message:**
```
client intended to send too large body
```

**Cause:**
- File exceeds `client_max_body_size` (50MB)

**Nginx Log:**
```
2024/03/23 10:00:00 [error] client intended to send too large body: 60000000 bytes
```

**Solution:**
```nginx
# Increase limit (if needed)
client_max_body_size 100M;
```

**User Message:**
"File too large. Maximum size is 50MB."

---

### 2. 502 Bad Gateway

**HTTP Status:** 502

**Error Message:**
```
502 Bad Gateway
nginx/1.29.5
```

**Cause:**
- Python proxy not running
- vLLM server not running
- Network connectivity issue

**Nginx Log:**
```
2024/03/23 10:00:00 [error] connect() failed (111: Connection refused) while connecting to upstream
```

**Solution:**
```bash
# Check services
docker compose ps

# Restart failed services
docker compose restart proxy vllm-server
```

---

### 3. 504 Gateway Timeout

**HTTP Status:** 504

**Error Message:**
```
504 Gateway Timeout
```

**Cause:**
- vLLM taking too long
- Proxy timeout too short

**Nginx Configuration:**
```nginx
# Increase timeouts
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

---

## Python Proxy Errors

### 1. No File Provided

**HTTP Status:** 400

**Error Response:**
```json
{
  "error": "No file provided"
}
```

**Cause:**
- Missing 'file' field in FormData
- Empty file upload

**Code:**
```python
if 'file' not in request.files:
    return jsonify({'error': 'No file provided'}), 400
```

---

### 2. Audio Conversion Failed

**HTTP Status:** 400

**Error Response:**
```json
{
  "error": "Audio conversion failed: ffmpeg failed: Invalid data found when processing input"
}
```

**Cause:**
- Corrupted audio file
- Unsupported codec
- ffmpeg not installed

**Proxy Log:**
```
🔄 Converting audio/webm → WAV...
❌ Conversion failed: ffmpeg failed: Invalid data found when processing input
```

**Solution:**
```python
try:
    wav_bytes = convert_audio_to_wav(audio_bytes)
except Exception as e:
    print(f"❌ Conversion failed: {e}")
    return jsonify({'error': f'Audio conversion failed: {str(e)}'}), 400
```

**User Message:**
"Audio conversion failed. Please try a different file format (WAV recommended)."

---

### 3. No Speech Detected

**HTTP Status:** 200

**Error Response:**
```json
{
  "text": "",
  "status": "no_speech",
  "audio_info": {
    "silence_ratio": 0.95,
    "rms_energy": 0.005
  },
  "tip": "Speak louder and closer to microphone"
}
```

**Cause:**
- Audio is mostly silence
- Speaking too quietly
- Microphone too far from mouth
- Background noise overwhelming speech

**Detection Logic:**
```python
has_speech = (
    duration >= 1.0 and      # At least 1 second
    rms_energy > 0.01 and    # Minimum energy
    silence_ratio < 0.9 and  # Less than 90% silence
    max_amp > 0.05           # Minimum amplitude
)
```

**User Message:**
"No speech detected. Please speak louder and closer to the microphone."

---

### 4. Accumulating Audio

**HTTP Status:** 200

**Response:**
```json
{
  "text": "",
  "status": "accumulating",
  "buffered_bytes": 50000,
  "required_bytes": 96000,
  "audio_info": {...}
}
```

**Cause:**
- Audio chunks being buffered
- Not enough audio collected yet (< 96KB)

**Not an Error:** This is expected behavior when accumulation is enabled.

**User Message:**
"⏳ Buffering audio... 52% (collecting more audio for better accuracy)"

---

### 5. vLLM Connection Error

**HTTP Status:** 500

**Error Response:**
```json
{
  "error": "vLLM error: HTTPConnectionPool(host='vllm', port=8000): Max retries exceeded"
}
```

**Cause:**
- vLLM server not running
- Network connectivity issue
- vLLM crashed

**Proxy Log:**
```
📤 Sending to vLLM: 112000 bytes...
❌ Error: HTTPConnectionPool(host='vllm', port=8000): Max retries exceeded
```

**Solution:**
```bash
# Check vLLM status
docker compose ps vllm-server

# Restart vLLM
docker compose restart vllm-server

# Check logs
docker logs vllm-server
```

---

## vLLM Server Errors

### 1. CUDA Out of Memory

**Error Message:**
```
RuntimeError: CUDA out of memory. Tried to allocate 9.54 GiB.
GPU 0 has a total capacity of 11.49 GiB of which 6.17 GiB is free.
```

**Cause:**
- Model too large for available VRAM
- Other processes using GPU memory
- `--gpu-memory-utilization` too high

**vLLM Log:**
```
(EngineCore_DP0 pid=173) ERROR torch.OutOfMemoryError: CUDA out of memory.
```

**Solution:**
```yaml
# docker-compose.yml
command:
  - --gpu-memory-utilization
  - "0.5"  # Reduce from 0.6 to 0.5
  - --max-model-len
  - "256"  # Reduce from 512 to 256
```

**Prevention:**
- Close other GPU applications
- Reduce model size
- Use smaller batch sizes

---

### 2. Model Loading Failed

**Error Message:**
```
OSError: Unable to load model: ibm-granite/granite-4.0-1b-speech
```

**Cause:**
- Invalid HF_TOKEN
- Model not downloaded
- Network issue downloading model

**vLLM Log:**
```
(APIServer pid=1) ERROR OSError: Unable to load model
```

**Solution:**
```bash
# Check HF token
cat .env

# Clear model cache
rm -rf ~/.cache/huggingface/hub/*

# Restart vLLM
docker compose restart vllm-server
```

---

### 3. Format Not Recognized

**Error Message:**
```
LibsndfileError: Error opening <_io.BytesIO object>: Format not recognised.
```

**Cause:**
- Corrupted WAV file
- Invalid WAV header
- Empty audio data

**vLLM Log:**
```
(APIServer pid=1) ERROR soundfile.LibsndfileError: Error opening <_io.BytesIO object>: Format not recognised.
```

**Solution:**
- Ensure ffmpeg conversion produces valid WAV
- Validate WAV header before sending
- Check audio_bytes length > 0

---

### 4. Token Limit Exceeded

**Error Message:**
```
ValueError: max_tokens=200 cannot be greater than max_model_len=128
```

**Cause:**
- Requested tokens exceed model limit

**Solution:**
```python
# In vLLM command
--max-model-len 512  # Increase limit
```

```python
# In request
"max_tokens": 100  # Reduce requested tokens
```

---

## GPU/Hardware Errors

### 1. NVIDIA Driver Error

**Error Message:**
```
NVIDIA driver error: CUDA_ERROR_INSUFFICIENT_DRIVER
```

**Cause:**
- NVIDIA driver not installed
- Driver version too old
- Driver crashed

**System Log:**
```
nvidia-smi: command not found
```

**Solution:**
```bash
# Check driver
nvidia-smi

# Install/update driver
sudo apt install nvidia-driver-535

# Reboot
sudo reboot
```

---

### 2. NVIDIA Container Toolkit Error

**Error Message:**
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

**Cause:**
- NVIDIA Container Toolkit not installed
- Docker not configured for GPU

**Solution:**
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

### 3. GPU Not Detected

**Error Message:**
```
No CUDA-capable device is detected
```

**Cause:**
- GPU not installed
- GPU disabled in BIOS
- Wrong GPU driver

**Solution:**
```bash
# Check GPU
lspci | grep -i nvidia
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

## Model Errors

### 1. Unsupported Language

**Error Message:**
```
Warning: Language 'xyz' not supported. Using English.
```

**Cause:**
- Granite Speech supports limited languages
- Auto-detection failed

**Supported Languages:**
- English (EN)
- French (FR)
- German (DE)
- Spanish (ES)
- Portuguese (PT)
- Japanese (JA)

**User Message:**
"Non-English audio detected. For best results, please speak in English, French, German, Spanish, Portuguese, or Japanese."

---

### 2. Poor Transcription Quality

**Symptoms:**
- Incorrect words
- Missing words
- Gibberish output

**Causes:**
- Background noise
- Heavy accent
- Technical jargon
- Multiple speakers
- Poor audio quality

**Solutions:**
- Reduce background noise
- Speak clearly and slowly
- Use high-quality microphone
- Keep mic close to mouth (6-12 inches)
- Enable "Accumulate audio" for better accuracy

---

## Error Prevention Strategies

### 1. Input Validation

```python
@app.route('/v1/audio/transcriptions', methods=['POST'])
def transcribe():
    # Validate file exists
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Validate file size
    audio_bytes = file.read()
    if len(audio_bytes) == 0:
        return jsonify({'error': 'Empty file'}), 400
    
    # Validate file type
    if not file.content_type.startswith('audio/'):
        return jsonify({'error': 'Not an audio file'}), 400
```

### 2. Graceful Degradation

```python
try:
    wav_bytes = convert_audio_to_wav(audio_bytes)
except Exception as e:
    return jsonify({
        'error': 'Audio conversion failed',
        'details': str(e),
        'suggestion': 'Try WAV format for best compatibility'
    }), 400
```

### 3. Clear Error Messages

```javascript
function showError(error) {
    let message;
    
    if (error.name === 'NotAllowedError') {
        message = 'Microphone access denied. Please allow microphone access in your browser settings.';
    } else if (error.name === 'NotFoundError') {
        message = 'No microphone found. Please connect a microphone and try again.';
    } else if (error.message.includes('timeout')) {
        message = 'Request timed out. Please try with a shorter audio clip.';
    } else {
        message = 'An error occurred: ' + error.message;
    }
    
    showStatus('❌ ' + message, 'alert-error');
}
```

### 4. Retry Logic

```javascript
async function transcribeWithRetry(audioBlob, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await transcribeChunk(audioBlob);
        } catch (error) {
            if (i === maxRetries - 1) {
                throw error; // Last attempt failed
            }
            // Wait before retry (exponential backoff)
            await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
        }
    }
}
```

---

## Error Monitoring

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/v1/audio/transcriptions', methods=['POST'])
def transcribe():
    try:
        # ... processing ...
        logger.info(f"✅ Transcription successful: {result['text'][:50]}")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
```

### Metrics to Monitor

1. **Error Rate:** Failed requests / Total requests
2. **Latency:** Average processing time
3. **GPU Utilization:** % of GPU in use
4. **VRAM Usage:** GB of VRAM used
5. **Queue Depth:** Number of pending requests

---

**This error reference provides comprehensive coverage of all known errors, their causes, and solutions.**
