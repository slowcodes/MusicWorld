from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize, low_pass_filter, high_pass_filter
import os


def remaster_audio_with_pydub(
        input_path: str,
        output_path: str,
        target_loudness: float = -14.0,  # LUFS (common for streaming)
        compression_threshold: float = -20.0,  # dB
        compression_ratio: float = 4.0,  # 4:1 ratio
        highpass_cutoff: int = 80,  # Hz (remove rumble)
        lowpass_cutoff: int = 15000,  # Hz (reduce harshness)
        reverb_dryness: float = 0.8,  # 0.0 (full reverb) to 1.0 (dry)
        normalize_audio: bool = True,
) -> bool:
    """
    Remasters audio using Pydub with professional effects chain.

    Args:
        input_path (str): Path to input WAV file.
        output_path (str): Path to save remastered WAV.
        target_loudness (float): Target loudness in dBFS (-14 to -10 is standard).
        compression_threshold (float): Compression threshold in dB.
        compression_ratio (float): Compression ratio (e.g., 4:1).
        highpass_cutoff (int): High-pass filter cutoff frequency.
        lowpass_cutoff (int): Low-pass filter cutoff frequency.
        reverb_dryness (float): Dry/wet mix (0.0 = full reverb, 1.0 = dry).
        normalize_audio (bool): Whether to normalize output to target loudness.

    Returns:
        bool: True if successful, False if failed.
    """
    try:
        # 1. Load audio file
        audio = AudioSegment.from_wav(input_path)

        # 2. Convert mono to stereo if needed
        if audio.channels == 1:
            audio = audio.set_channels(2)

        # 3. Apply high-pass filter (remove rumble)
        audio = high_pass_filter(audio, cutoff=highpass_cutoff)

        # 4. Apply low-pass filter (smooth highs)
        audio = low_pass_filter(audio, cutoff=lowpass_cutoff)

        # 5. Dynamic range compression
        audio = compress_dynamic_range(
            audio,
            threshold=compression_threshold,
            ratio=compression_ratio
        )

        # 6. Add subtle reverb (if enabled)
        if reverb_dryness < 1.0:
            wet_signal = audio - 6  # Reduce volume for wet signal
            wet_signal = wet_signal.set_frame_rate(int(audio.frame_rate * 0.8))  # Simulate reverb
            audio = audio.overlay(wet_signal, gain_during_overlay=-10 * (1 - reverb_dryness))

        # 7. Normalize to target loudness
        if normalize_audio:
            audio = normalize(audio, headroom=abs(target_loudness))

        # 8. Export as WAV (16-bit PCM)
        audio.export(output_path, format="wav", parameters=["-ac", "2", "-ar", "44100"])
        return True

    except Exception as e:
        print(f"⚠️ Remastering failed: {str(e)}")
        # Clean up failed output
        if os.path.exists(output_path):
            os.remove(output_path)
        return False