from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
import torch
import torchaudio
import io
import os

app = FastAPI(title="Granite Speech Transcription API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
MODEL_NAME = "ibm-granite/granite-4.0-1b-speech"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

print(f"Loading model on {DEVICE} with dtype {DTYPE}...")

# Load model and processor
processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_NAME,
    torch_dtype=DTYPE,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    device_map="auto" if DEVICE == "cuda" else None
)

if DEVICE == "cuda":
    model.to(DEVICE)

model.eval()
print("Model loaded successfully!")


@app.get("/health")
async def health_check():
    """Check if the service is running"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": DEVICE,
        "dtype": str(DTYPE)
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile):
    """
    Transcribe audio file using Granite speech model
    """
    try:
        # Read audio file
        audio_bytes = await file.read()
        
        # Load audio with torchaudio
        audio_buffer = io.BytesIO(audio_bytes)
        waveform, sample_rate = torchaudio.load(audio_buffer)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        
        # Create text prompt
        user_prompt = "<|audio|>can you transcribe the speech into a written format?"
        chat = [
            {"role": "user", "content": user_prompt},
        ]
        prompt = processor.tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True
        )
        
        # Process inputs
        inputs = processor(
            prompt,
            waveform.squeeze(0),
            sampling_rate=16000,
            return_tensors="pt"
        )
        
        if DEVICE == "cuda":
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        
        # Generate transcription
        with torch.inference_mode():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=False,
                num_beams=1
            )
        
        # Decode output
        num_input_tokens = inputs["input_ids"].shape[-1]
        new_tokens = generated_ids[0, num_input_tokens:].unsqueeze(0)
        output_text = processor.batch_decode(
            new_tokens, add_special_tokens=False, skip_special_tokens=True
        )[0]
        
        return {
            "success": True,
            "text": output_text,
            "device": DEVICE
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/transcribe/chunk")
async def transcribe_chunk(file: UploadFile):
    """
    Transcribe audio chunk (for streaming/mic input)
    """
    return await transcribe(file)
