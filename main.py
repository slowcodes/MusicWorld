from fastapi import FastAPI, UploadFile, File, HTTPException, Form
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
from libs.pydub_impl import remaster_audio_with_pydub

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
import uuid
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matchering_api")


@app.post("/remaster-audio/")
async def upload_and_remaster(file: UploadFile = File(...), tool: str = Form(...)):
    """Endpoint that handles file upload and remastering"""
    upload_path = None
    output_path = None
    logger.info(f"Received file: {file.filename} using tool: {tool}")
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
        if tool == "Pedalboard":
            success = pedalboard_remaster_audio(upload_path, output_path)
            logger.info(f"Remastering completed with Pedalboard: {success}")
        elif tool == "Pydub":
            success = remaster_audio_with_pydub(
                upload_path,
                output_path,
                target_loudness=-12.0,  # Slightly louder than streaming standard
                compression_ratio=3.0,  # More transparent compression
                highpass_cutoff=60,  # Less aggressive low-end cut
                reverb_dryness=0.9  # Very subtle reverb
            )
            logger.info(f"Remastering completed with Pydub: {success}")
        elif tool == "Matchering":
            # Using matchering for remastering
            success = mg.process(
                target=str(upload_path),
                reference=str(upload_path),  # Use the same file as reference
                output=str(output_path)
            )
            logger.info(f"Remastering completed with Matchering: {success}")
        else:
            raise HTTPException(400, "Unsupported remastering tool specified")

        if not success:
            raise HTTPException(500, "Audio remastering failed")

        # Return the processed file
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=output_path.name
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
