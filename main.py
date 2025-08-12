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

from libs.pedalboard import remaster_audio_with_pedalboard

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
    allow_origins=["http://13.61.6.255:4200"],
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


def validate_audio_file(file_path: str) -> dict:
    """Comprehensive audio validation with detailed checks"""
    validation = {
        "is_valid": False,
        "sample_rate": None,
        "channels": None,
        "duration": None,
        "subtype": None,
        "issues": []
    }

    try:
        with sf.SoundFile(file_path) as audio:
            validation.update({
                "sample_rate": audio.samplerate,
                "channels": audio.channels,
                "duration": len(audio) / audio.samplerate,
                "subtype": audio.subtype
            })

            # Check requirements
            if audio.samplerate != 44100:
                validation["issues"].append(f"Invalid sample rate: {audio.samplerate} (needs 44100)")
            if audio.channels != 2:
                validation["issues"].append(f"Invalid channels: {audio.channels} (needs stereo)")
            if audio.subtype not in ['PCM_16', 'PCM_24', 'PCM_32']:
                validation["issues"].append(f"Unsupported format: {audio.subtype} (needs PCM)")
            if len(audio) / audio.samplerate < 3:
                validation["issues"].append("Audio too short (needs ≥3 seconds)")

        validation["is_valid"] = len(validation["issues"]) == 0
        return validation

    except Exception as e:
        validation["issues"].append(f"Validation error: {str(e)}")
        return validation


def prepare_audio(input_path: str) -> str:
    """Convert audio to Matchering-compatible format"""
    try:
        # Validate first
        validation = validate_audio_file(input_path)
        if validation["is_valid"]:
            return input_path

        logger.info(f"Audio needs conversion: {validation['issues']}")

        # Create output path
        output_path = os.path.join(PROCESSED_FOLDER, f"prepared_{uuid.uuid4()}.wav")

        # Convert using pydub
        audio = AudioSegment.from_wav(input_path)

        # Apply fixes
        if validation["sample_rate"] != 44100:
            audio = audio.set_frame_rate(44100)
        if validation["channels"] != 2:
            audio = audio.set_channels(2)
        if validation["duration"] < 3:
            # Pad with silence if too short
            silence = AudioSegment.silent(duration=3000 - len(audio) + 100, frame_rate=44100)
            audio = audio + silence

        # Export with correct format
        audio.export(
            output_path,
            format="wav",
            parameters=["-ac", "2", "-ar", "44100"]
        )

        return output_path

    except Exception as e:
        logger.error(f"Audio preparation failed: {str(e)}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return None


def process_with_matchering(input_path: str) -> str:
    """Core processing with enhanced error handling"""
    output_path = os.path.join(PROCESSED_FOLDER, f"remastered_{uuid.uuid4()}.wav")

    try:
        logger.info(f"Starting processing for {input_path}")

        # Process with timeout
        try:
            mg.process(
                target=input_path,
                results=output_path,
                reference=None
            )
        except Exception as e:
            raise RuntimeError(f"Matchering error: {str(e)}")

        # Verify output
        if not os.path.exists(output_path):
            raise RuntimeError("No output file created")
        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Empty output file")

        return output_path

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise


@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    temp_path = None
    prepared_path = None

    try:
        # Validate file type
        if not file.filename.lower().endswith('.wav'):
            raise HTTPException(400, "Only WAV files supported")

        # Save upload
        temp_path = os.path.join(UPLOAD_FOLDER, f"upload_{uuid.uuid4()}.wav")
        with open(temp_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Prepare audio
        prepared_path = prepare_audio(temp_path)
        if not prepared_path:
            raise HTTPException(400, "Invalid audio format")

        # Process
        # output_path = process_with_matchering(prepared_path)
        output_path = remaster_audio_with_pedalboard(
            prepared_path,
            'processed/pedalboard_remastered.wav',
            target_lufs=-12.0,
            compression_ratio=3.0
        )

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="remastered.wav"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        raise HTTPException(500, f"Processing failed: {str(e)}")
    finally:
        # Cleanup
        for path in [temp_path, prepared_path]:
            if path and os.path.exists(path):
                os.remove(path)