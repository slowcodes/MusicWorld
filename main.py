from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
from pydub import AudioSegment
from starlette.middleware.cors import CORSMiddleware
import matchering as mg
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
        # Verify WAV format
        if not file.filename.lower().endswith('.wav'):
            raise HTTPException(400, "Only WAV files supported")

        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

        # Process audio
        processed_path = matchering_remaster_audio(file_path)

        if not processed_path:
            raise HTTPException(500, "Audio remastering failed")

        return FileResponse(
            processed_path,
            media_type="audio/wav",
            filename="remastered.wav"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Server error: {str(e)}")


async def remaster_audio(file_path: str) -> str:
    # Load audio using pydub
    sound = AudioSegment.from_file(file_path)

    # Example "remastering": Normalize volume and reduce noise
    normalized = sound.normalize()

    # Export to wav (for now, simple remastering)
    processed_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")
    normalized.export(processed_path, format="wav")

    return processed_path


def validate_wav_file(file_path: str) -> bool:
    """Verify the WAV file meets Matchering's requirements"""
    try:
        # Check basic file properties
        if not os.path.exists(file_path):
            return False

        if os.path.getsize(file_path) == 0:
            return False

        # Verify audio properties using soundfile
        import soundfile as sf
        with sf.SoundFile(file_path) as audio:
            if audio.samplerate != 44100:
                raise ValueError(f"Invalid sample rate: {audio.samplerate} (needs 44100)")
            if audio.channels != 2:
                raise ValueError(f"Invalid channels: {audio.channels} (needs stereo)")
            if audio.subtype != 'PCM_16':
                print(f"Warning: PCM_16 is recommended, found {audio.subtype}")

        return True
    except Exception as e:
        print(f"WAV validation failed: {str(e)}")
        return False


def matchering_remaster_audio(input_audio_path: str) -> str:
    """Optimized processing for WAV files"""
    try:
        # 1. Validate input WAV
        if not validate_wav_file(input_audio_path):
            raise ValueError("Invalid WAV file format")

        # 2. Prepare output
        output_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")
        if os.path.exists(output_path):
            os.remove(output_path)

        # 3. Process with error handling
        try:
            mg.process(
                input_audio_path,  # Original WAV file
                output_path,  # Output file
                None  # No reference
            )
        except Exception as e:
            raise RuntimeError(f"Processing error: {str(e)}")

        # 4. Validate output
        if not os.path.exists(output_path):
            raise RuntimeError("No output file created")
        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Empty output file")

        return output_path

    except Exception as e:
        print(f"Remastering error: {str(e)}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return None