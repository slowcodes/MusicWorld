from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
from pydub import AudioSegment
from starlette.middleware.cors import CORSMiddleware
import matchering as mg
import uuid
import soundfile as sf

from pathlib import Path

# from rematering_libs.matchering import matchering_remaster_audio

app = FastAPI()

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://13.61.6.255:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/all-remastered")
async def smoot():
    return {"message": "Hello World"}


@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Validate extension
        if not file.filename.lower().endswith('.wav'):
            raise HTTPException(400, "Only WAV files supported")

        # Create temp file
        temp_path = os.path.join(UPLOAD_FOLDER, f"upload_{uuid.uuid4()}.wav")
        with open(temp_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Process with enhanced validation
        output_path = matchering_remaster_audio(temp_path)
        if not output_path:
            raise HTTPException(500, "Audio remastering failed")

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="remastered.wav"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)


async def remaster_audio(file_path: str) -> str:
    # Load audio using pydub
    sound = AudioSegment.from_file(file_path)

    # Example "remastering": Normalize volume and reduce noise
    normalized = sound.normalize()

    # Export to wav (for now, simple remastering)
    processed_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")
    normalized.export(processed_path, format="wav")

    return processed_path


def validate_and_fix_wav(input_path: str) -> str:
    """Ensure the WAV meets all Matchering requirements"""
    try:
        # Read file metadata
        with sf.SoundFile(input_path) as f:
            sr = f.samplerate
            channels = f.channels
            subtype = f.subtype
            duration = len(f) / sr

        # Check minimum duration (Matchering needs at least 3 seconds)
        if duration < 3:
            raise ValueError(f"Audio too short: {duration:.1f}s (needs ≥3s)")

        # Prepare output path
        output_path = os.path.join(PROCESSED_FOLDER, f"fixed_{uuid.uuid4()}.wav")

        # Only convert if needed
        if sr == 44100 and channels == 2 and subtype == 'PCM_16':
            return input_path

        # Convert using pydub (more reliable than direct soundfile)
        audio = AudioSegment.from_wav(input_path)
        audio = audio.set_frame_rate(44100)
        audio = audio.set_channels(2)
        audio = audio.set_sample_width(2)  # 16-bit
        audio.export(output_path, format="wav", parameters=["-ac", "2", "-ar", "44100"])

        return output_path

    except Exception as e:
        print(f"Validation failed: {str(e)}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return None


def matchering_remaster_audio(input_audio_path: str) -> str:
    """Robust processing with full validation"""
    try:
        # 1. Validate and fix if needed
        processed_path = validate_and_fix_wav(input_audio_path)
        if not processed_path:
            raise ValueError("Invalid audio format")

        # 2. Prepare output
        output_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")
        if os.path.exists(output_path):
            os.remove(output_path)

        # 3. Process with volume normalization
        try:
            # Normalize volume first if too quiet
            audio = AudioSegment.from_wav(processed_path)
            if audio.dBFS < -30:  # Too quiet
                audio = audio.apply_gain(-audio.dBFS - 10)
                normalized_path = os.path.join(PROCESSED_FOLDER, f"norm_{uuid.uuid4()}.wav")
                audio.export(normalized_path, format="wav")
                processed_path = normalized_path

            mg.process(
                processed_path,
                output_path,
                None
            )
        except Exception as e:
            raise RuntimeError(f"Processing error: {str(e)}")

        # 4. Validate output
        if not os.path.exists(output_path):
            raise RuntimeError("No output file created")
        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Empty output file")

        return output_path

    finally:
        # Clean up temporary files
        for path in [processed_path, normalized_path] if 'processed_path' in locals() else []:
            if path and path != input_audio_path and os.path.exists(path):
                os.remove(path)
