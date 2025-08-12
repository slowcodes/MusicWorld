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

from libs.pedalboard_impl import pedalboard_remaster_audio

# from libs.matchering import matchering_remaster_audio

app = FastAPI()

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import logging
from pydub import AudioSegment
import uuid
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matchering_api")


@app.post("/remaster-audio/")
async def upload_and_remaster(file: UploadFile = File(...)):
    """Endpoint that handles file upload and remastering"""
    upload_path = None
    output_path = None

    try:
        # Validate file type
        if not file.filename.lower().endswith('.wav'):
            raise HTTPException(400, "Only WAV files are supported")

        # Create unique filenames
        file_id = uuid.uuid4()
        upload_path = Path(UPLOAD_FOLDER) / f"upload_{file_id}.wav"
        output_path = Path(PROCESSED_FOLDER) / f"remastered_{file_id}.wav"

        # Save uploaded file
        with upload_path.open("wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

        # Process audio
        success = pedalboard_remaster_audio(upload_path, output_path)
        if not success:
            raise HTTPException(500, "Audio remastering failed")

        # Return the processed file
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
        # Clean up temporary files
        if upload_path and upload_path.exists():
            upload_path.unlink()
        # Note: output_path is not deleted here as it's being returned
