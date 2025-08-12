from fastapi import FastAPI, UploadFile, File
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
        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process / "Remaster" the file with pydub
        # processed_path = await remaster_audio(file_path)

        # Remaster file with matchring
        processed_path = matchering_remaster_audio(
            file_path
        )
        if not processed_path:
            raise Exception("Audio remastering failed")
        print(f"Remastered file saved at: {processed_path}")

        # return FileResponse(processed_path, media_type="audio/wav", filename="remastered.wav")
        return FileResponse(processed_path, media_type="audio/wav", filename="remastered.wav")
    except Exception as e:
        return {"error": str(e)}


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
    FINAL WORKING VERSION for Matchering 2.0.6
    """
    try:
        output_path = os.path.join(PROCESSED_FOLDER, "remastered.wav")

        # THE ONLY WORKING SYNTAX
        mg.process(
            target=input_audio_path,  # Your input file
            results=output_path,  # Output file
            reference=None,  # Must be explicitly None
            reference2=None  # Must be explicitly None
        )

        return output_path

    except Exception as e:
        print(f"Remastering failed: {str(e)}")
        return None