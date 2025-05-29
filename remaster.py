import gradio as gr
import torchaudio
import subprocess
import os
from demucs.apply import apply_model
from demucs.pretrained import get_model
from fastapi.middleware.cors import CORSMiddleware

# Load Demucs AI model
model = get_model(name='htdemucs')  # High-quality model for remastering

def remaster_audio(audio_file):
    # Save the uploaded audio
    input_path = audio_file
    output_dir = "remastered_output"

    # Clean up old outputs
    if os.path.exists(output_dir):
        subprocess.run(["rm", "-rf", output_dir])
    os.makedirs(output_dir, exist_ok=True)

    # Run the AI model to separate/remaster
    sources = apply_model(model, input_path, device='cpu', overlap=0.25, shifts=1)

    # Save just the "mixture" or remastered version (optional: mix stems back)
    mixture = sources['mixture']
    remastered_path = os.path.join(output_dir, "remastered.wav")
    torchaudio.save(remastered_path, mixture[None], 44100)

    return remastered_path

# Gradio Interface
interface = gr.Interface(
    fn=remaster_audio,
    inputs=gr.Audio(type="filepath", label="Upload Music File"),
    outputs=gr.Audio(type="filepath", label="Remastered Output"),
    title="AI Music Remastering",
    description="Upload a music file and get a remastered version using an AI model."
)

interface.launch()
