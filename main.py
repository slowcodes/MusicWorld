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


def matchering_remaster_audio(input_audio_path: str) -> str:
    """
    Complete implementation with full error handling
    """
    try:
        # Create processed directory if needed
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)

        output_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")

        # Verify input file exists and is valid
        if not os.path.exists(input_audio_path):
            raise ValueError("Input file does not exist")

        if os.path.getsize(input_audio_path) == 0:
            raise ValueError("Input file is empty")

        # Process with error context
        try:
            mg.process(
                input_audio_path,  # Input file
                output_path,  # Output file
                None  # Reference (None for no reference)
            )
        except Exception as e:
            raise RuntimeError(f"Matchering processing failed: {str(e)}")

        # Verify output was created
        if not os.path.exists(output_path):
            raise RuntimeError("Output file was not created")

        if os.path.getsize(output_path) == 0:
            os.remove(output_path)
            raise RuntimeError("Output file is empty")

        return output_path

    except Exception as e:
        print(f"Remastering error: {str(e)}")
        # Clean up failed output file if exists
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return None