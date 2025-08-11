import os
from pathlib import Path
import matchering as mg


def matchering_remaster_audio(input_audio_path: Path):
    """
    Remasters an audio file using matchering v2.0.6
    and saves it as 'processed/remastered.wav'.

    Args:
        input_audio_path (Path): Path object to the audio file to be remastered.
    """
    if not input_audio_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_audio_path}")

    # Ensure 'processed' directory exists
    output_dir = Path("processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output file path
    output_file_path = output_dir / "remastered.wav"

    # Perform mastering
    mg.process(
        target=str(input_audio_path),
        reference=str(input_audio_path),  # Replace with professional reference for better results
        output=str(output_file_path)
    )

    print(f"Remastered audio saved at: {output_file_path}")
