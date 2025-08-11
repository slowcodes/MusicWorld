from pathlib import Path
import matchering as mg
from typing import Union


def matchering_remaster_audio(
        audio_path: Union[str, Path],
        reference_path: Union[str, Path],
        bit_depth: str = "24"
) -> Path:
    """
    Remaster an audio file using Matchering v2.0.6 (old API style).
    Saves output as 'processed/remastered.wav'.
    """
    audio_path = Path(audio_path).expanduser().resolve()
    reference_path = Path(reference_path).expanduser().resolve()

    bitdepth_map = {
        "16": mg.pcm16,
        "24": mg.pcm24,
        "32f": mg.pcm32f
    }
    if bit_depth not in bitdepth_map:
        raise ValueError(f"bit_depth must be one of {set(bitdepth_map.keys())}")

    processed_dir = audio_path.parent / "processed"
    processed_dir.mkdir(exist_ok=True)
    output_file = processed_dir / "remastered.wav"

    mg.process(
        target=str(audio_path),
        reference=str(reference_path),
        results=[bitdepth_map[bit_depth](str(output_file))]
    )

    if not output_file.exists():
        raise RuntimeError(f"Matchering finished but no output file created: {output_file}")

    return output_file
