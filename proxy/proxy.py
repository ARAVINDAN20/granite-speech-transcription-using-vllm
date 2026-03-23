#!/usr/bin/env python3
"""
Audio Proxy Server for Granite Speech
- Converts ANY audio format (WebM, MP3, WAV, etc.) to WAV/PCM using ffmpeg
- Accumulates audio chunks for better transcription
- Provides CORS support for browser access
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import base64
import io
import tempfile
import os
import requests
import time
from collections import defaultdict

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

VLLM_URL = os.environ.get('VLLM_URL', 'http://localhost:8000')

# Store accumulated audio per session
audio_buffers = defaultdict(list)

def convert_audio_to_wav(audio_bytes: bytes) -> bytes:
    """Convert any audio format to WAV/PCM using ffmpeg."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.input') as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_out:
        tmp_out_path = tmp_out.name
    
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', tmp_in_path,
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            '-af', 'volume=3.0',  # 3x volume boost
            tmp_out_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:200]}")
        
        with open(tmp_out_path, 'rb') as f:
            wav_bytes = f.read()
        
        if len(wav_bytes) < 1000:
            raise RuntimeError("Converted WAV too small")
        
        return wav_bytes
        
    finally:
        for path in [tmp_in_path, tmp_out_path]:
            if os.path.exists(path):
                os.unlink(path)

def analyze_audio(wav_bytes: bytes) -> dict:
    """Analyze audio to check if it contains speech."""
    try:
        import librosa
        y, sr = librosa.load(io.BytesIO(wav_bytes), sr=16000, mono=True)
        
        duration = len(y) / sr
        rms = float(librosa.feature.rms(y=y)[0].mean())
        silence_ratio = float((abs(y) < 0.01).mean())
        max_amp = float(abs(y).max())
        
        has_speech = (duration >= 1.0 and rms > 0.01 and silence_ratio < 0.9 and max_amp > 0.05)
        
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
    except Exception as e:
        return {'valid': False, 'error': str(e)}

@app.route('/v1/audio/transcriptions', methods=['POST'])
def transcribe():
    """Handle audio transcription with format conversion."""
    start_time = time.time()
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        model = request.form.get('model', 'ibm-granite/granite-4.0-1b-speech')
        session_id = request.form.get('session_id', 'default')
        accumulate = request.form.get('accumulate', 'true').lower() == 'true'
        
        audio_bytes = file.read()
        file_size = len(audio_bytes)
        filename = file.filename or 'audio'
        
        print(f"📥 Received: {filename}, {file_size} bytes, type: {file.content_type}")
        
        # Convert to WAV (handles WebM, MP3, WAV, etc.)
        print(f"🔄 Converting {file.content_type or 'unknown'} → WAV...")
        try:
            wav_bytes = convert_audio_to_wav(audio_bytes)
            print(f"✅ Converted: {len(wav_bytes)} bytes WAV")
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            return jsonify({'error': f'Audio conversion failed: {str(e)}'}), 400
        
        # Analyze audio
        audio_info = analyze_audio(wav_bytes)
        print(f"🔍 Audio analysis: {audio_info}")
        
        # Accumulate if requested
        if accumulate:
            audio_buffers[session_id].append(wav_bytes)
            total_size = sum(len(b) for b in audio_buffers[session_id])
            
            if total_size < 96000:  # Need ~96KB (~3 seconds)
                return jsonify({
                    'text': '',
                    'status': 'accumulating',
                    'buffered_bytes': total_size,
                    'required_bytes': 96000,
                    'audio_info': audio_info
                }), 200
            
            # Combine buffers
            combined = b''.join(audio_buffers[session_id])
            audio_buffers[session_id] = []
            wav_bytes = combined
            print(f"🔗 Accumulated: {len(wav_bytes)} bytes")
        
        # Check for speech
        if not audio_info.get('has_speech', False):
            print("⚠️ No speech detected")
            return jsonify({
                'text': '',
                'status': 'no_speech',
                'audio_info': audio_info,
                'tip': 'Speak louder and closer to microphone'
            }), 200
        
        # Send to vLLM
        print(f"📤 Sending to vLLM: {len(wav_bytes)} bytes...")
        
        vllm_response = requests.post(
            f'{VLLM_URL}/v1/audio/transcriptions',
            files={'file': ('audio.wav', io.BytesIO(wav_bytes), 'audio/wav')},
            data={'model': model},
            timeout=90
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️ vLLM response: {vllm_response.status_code} in {elapsed:.2f}s")
        
        if vllm_response.status_code != 200:
            return jsonify({
                'error': 'vLLM error',
                'status': vllm_response.status_code,
                'response': vllm_response.text[:200]
            }), vllm_response.status_code
        
        result = vllm_response.json()
        result['_debug'] = {
            'audio_info': audio_info,
            'processing_time_sec': round(elapsed, 2),
            'input_bytes': len(wav_bytes),
            'accumulated': accumulate
        }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Proxy model listing."""
    try:
        resp = requests.get(f'{VLLM_URL}/v1/models', timeout=5)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check."""
    return jsonify({'status': 'healthy', 'proxy': 'running', 'vllm_url': VLLM_URL})

if __name__ == '__main__':
    print("🚀 Starting Audio Proxy on http://0.0.0.0:8080")
    print(f"📡 Forwarding to vLLM at {VLLM_URL}")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
