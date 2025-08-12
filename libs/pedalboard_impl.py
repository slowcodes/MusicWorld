import os
from pathlib import Path

import numpy as np
import soundfile as sf
from pedalboard import (
    Pedalboard,
    Compressor,
    Gain,
    Limiter,
    HighpassFilter,
    LowpassFilter,
    Reverb
)
from typing import Optional


def pedalboard_remaster_audio(input_path: Path, output_path: Path) -> bool:
    """Core remastering function with Pedalboard"""
    try:
        # Load audio file
        audio, sample_rate = sf.read(input_path)

        # Convert mono to stereo if needed
        if len(audio.shape) == 1:
            audio = np.column_stack((audio, audio))

        # Create effects chain
        board = Pedalboard([
            HighpassFilter(80.0),  # Remove low-end rumble
            LowpassFilter(15000.0),  # Reduce high-frequency harshness
            Compressor(
                threshold_db=-20.0,
                ratio=4.0,
                attack_ms=5.0,
                release_ms=100.0
            ),
            Gain(gain_db=2.0),  # Make-up gain
            Reverb(room_size=0.25, wet_level=0.15),  # Add subtle space
            Limiter(threshold_db=-14.0)  # Final loudness control
        ], sample_rate=sample_rate)

        # Process audio
        processed = board(audio, sample_rate)

        # Prevent clipping
        max_sample = np.max(np.abs(processed))
        if max_sample > 0.99:
            processed = processed * (0.99 / max_sample)

        # Save output
        sf.write(output_path, processed, sample_rate, subtype='PCM_16')
        return True

    except Exception as e:
        print(f"Remastering error: {str(e)}")
        # Clean up failed output
        if output_path.exists():
            output_path.unlink()
        return False