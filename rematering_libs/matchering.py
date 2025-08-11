import os
import matchering as mg


def matchering_remaster_audio(input_audio_path: str):
    """
    Remasters an audio file using matchering v2.0.6
    and saves it as 'processed/remastered.wav'.

    Args:
        input_audio_path (str): Path to the audio file to be remastered.
    """

    # Ensure 'processed' directory exists
    output_dir = "processed"
    os.makedirs(output_dir, exist_ok=True)

    # Output file path
    output_file_path = os.path.join(output_dir, "remastered.wav")

    # Perform mastering
    # Here, we use the input audio itself as both the target and reference
    # For better results, replace `reference` with a high-quality reference track
    mg.process(
        target=input_audio_path,
        reference=input_audio_path,  # You can replace with a reference track
        output=output_file_path
    )

    print(f"Remastered audio saved at: {output_file_path}")
