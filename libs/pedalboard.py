import os
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


def remaster_audio_with_pedalboard(
        input_path: str,
        output_path: str,
        *,
        target_lufs: float = -14.0,
        compression_ratio: float = 4.0,
        reverb_room_size: float = 0.25,
        highpass_cutoff: float = 80.0,
        lowpass_cutoff: float = 15000.0,
        make_up_gain_db: float = 2.0
) -> Optional[str]:
    """
    Remaster a WAV file using Pedalboard audio effects

    Args:
        input_path: Path to input WAV file
        output_path: Path to save remastered WAV file
        target_lufs: Target loudness level (-14 to -10 is typical for streaming)
        compression_ratio: Compression ratio (2.0-10.0)
        reverb_room_size: Reverb amount (0-1)
        highpass_cutoff: Highpass filter cutoff in Hz
        lowpass_cutoff: Lowpass filter cutoff in Hz
        make_up_gain_db: Additional gain after compression

    Returns:
        Path to output file if successful, None otherwise
    """
    try:
        # 1. Load audio file
        audio, sample_rate = sf.read(input_path)

        # Ensure stereo (convert mono to stereo if needed)
        if len(audio.shape) == 1:
            audio = np.column_stack((audio, audio))

        # 2. Create effects chain
        board = Pedalboard([
            HighpassFilter(highpass_cutoff),
            LowpassFilter(lowpass_cutoff),
            Compressor(
                threshold_db=-20.0,
                ratio=compression_ratio,
                attack_ms=5.0,
                release_ms=100.0
            ),
            Gain(make_up_gain_db),
            Reverb(room_size=reverb_room_size, wet_level=0.15),
            Limiter(threshold_db=target_lufs)
        ], sample_rate=sample_rate)

        # 3. Process audio
        processed = board(audio, sample_rate)

        # 4. Normalize to prevent clipping
        max_sample = np.max(np.abs(processed))
        if max_sample > 0.99:  # Close to clipping
            processed = processed * (0.99 / max_sample)

        # 5. Save output
        sf.write(output_path, processed, sample_rate, subtype='PCM_16')

        return output_path

    except Exception as e:
        print(f"Remastering failed: {str(e)}")
        # Clean up failed output if exists
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


# Example Usage:
if __name__ == "__main__":
    input_file = "input.wav"
    output_file = "remastered.wav"

    result = remaster_audio_with_pedalboard(
        input_file,
        output_file,
        target_lufs=-12.0,
        compression_ratio=3.0
    )

    if result:
        print(f"Successfully remastered to {result}")
    else:
        print("Remastering failed")