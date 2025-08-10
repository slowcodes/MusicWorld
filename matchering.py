from pathlib import Path
import tempfile
import shutil
import matchering as mg
from typing import Union


def matchering_remaster_audio(
        audio_path: Union[str, Path],
        reference_path: Union[str, Path],
        bit_depth: str = "24",
        log_fn=None
) -> Path:
    """
    Remaster an audio file using matchering and save as 'processed/remastered.wav'.

    Parameters
    ----------
    audio_path : str | Path
        Path to the audio file to remaster (target).
    reference_path : str | Path
        Path to the reference mastered track.
    bit_depth : str, default "24"
        Output bit depth: one of "16", "24", or "32f".
    log_fn : callable, optional
        Function to receive log messages (e.g., print).

    Returns
    -------
    Path
        Path to the remastered audio file.
    """
    audio_path = Path(audio_path).expanduser().resolve()
    reference_path = Path(reference_path).expanduser().resolve()

    bitdepth_map = {
        "16": mg.pcm16,
        "24": mg.pcm24,
        "32f": mg.pcm32f
    }

    if bit_depth not in bitdepth_map:
        raise ValueError("bit_depth must be one of '16', '24', or '32f'")

    # Ensure processed folder exists
    processed_dir = audio_path.parent / "processed"
    processed_dir.mkdir(exist_ok=True)

    # Always save as processed/remastered.wav
    output_file = processed_dir / "remastered.wav"

    if log_fn is not None:
        mg.log(log_fn)

    tmpdir = Path(tempfile.mkdtemp(prefix="matchering_"))

    try:
        mg.process(
            target=str(audio_path),
            reference=str(reference_path),
            results=[bitdepth_map[bit_depth](str(output_file))],
            tmpdir=str(tmpdir)
        )

        if not output_file.exists():
            raise RuntimeError(f"Matchering finished but no output file created: {output_file}")

        return output_file

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
