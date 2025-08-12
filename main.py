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
    DEBUGGABLE IMPLEMENTATION for Matchering 2.0.6
    """
    try:
        print(f"Debug: Input path exists? {os.path.exists(input_audio_path)}")
        print(f"Debug: Input file size: {os.path.getsize(input_audio_path)} bytes")

        output_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")
        print(f"Debug: Output path: {output_path}")

        # Attempt 1: Positional arguments
        try:
            mg.process(input_audio_path, output_path)
            print("Debug: Success with positional args")
            return output_path
        except Exception as e1:
            print(f"Debug: Positional args failed: {str(e1)}")

            # Attempt 2: Named arguments
            try:
                mg.process(target=input_audio_path, results=output_path)
                print("Debug: Success with named args")
                return output_path
            except Exception as e2:
                print(f"Debug: Named args failed: {str(e2)}")
                raise Exception(f"All attempts failed. PosErr: {e1}, NamedErr: {e2}")

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return None