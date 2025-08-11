from pathlib import Path
import matchering as mg
from typing import Union


def matchering_remaster_audio(
        audio_path: Union[str, Path],
        reference_path: Union[str, Path],
        bit_depth: str = "24"
) -> Path:
    """
    Remaster an audio file using Matchering v2.0.6 minimal API.
    Saves output as 'processed/remastered.wav'.
    """
    audio_path = Path(audio_path).expanduser().resolve()
    reference_path = Path(reference_path).expanduser().resolve()

    valid_bit_depths = {"16", "24", "32f"}
    if bit_depth not in valid_bit_depths:
        raise ValueError(f"bit_depth must be one of {valid_bit_depths}")

    processed_dir = audio_path.parent / "processed"
    processed_dir.mkdir(exist_ok=True)
    output_file = processed_dir / "remastered.wav"

    mg.process(
        target=str(audio_path),
        reference=str(reference_path),
        results=[{
            "type": "wav",
            "path": str(output_file),
            "bitdepth": bit_depth
        }]
    )

    if not output_file.exists():
        raise RuntimeError(f"Matchering finished but no output file created: {output_file}")

    return output_file
