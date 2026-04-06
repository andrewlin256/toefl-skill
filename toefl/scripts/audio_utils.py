#!/usr/bin/env python3
"""
Audio utilities for TOEFL exercise generation.
Generates beep tones, silence segments, and concatenates audio clips.

Uses pydub when available, falls back to raw WAV generation.
"""

import io
import math
import struct
import wave
import os

SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit


def generate_sine_wav(frequency: float, duration_ms: int, volume: float = 0.5) -> bytes:
    """Generate a sine wave as raw WAV bytes."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH)
        wav.setframerate(SAMPLE_RATE)
        max_amp = 32767 * volume
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            # Apply fade in/out (20ms) to avoid clicks
            fade_samples = int(SAMPLE_RATE * 0.02)
            if i < fade_samples:
                envelope = i / fade_samples
            elif i > n_samples - fade_samples:
                envelope = (n_samples - i) / fade_samples
            else:
                envelope = 1.0
            sample = int(max_amp * envelope * math.sin(2 * math.pi * frequency * t))
            wav.writeframes(struct.pack("<h", sample))
    return buf.getvalue()


def generate_silence_wav(duration_ms: int) -> bytes:
    """Generate silence as raw WAV bytes."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"\x00\x00" * n_samples)
    return buf.getvalue()


def save_wav(data: bytes, path: str):
    """Save raw WAV bytes to a file."""
    with open(path, "wb") as f:
        f.write(data)


def generate_beep_file(path: str, frequency: float = 880, duration_ms: int = 300, volume: float = 0.4):
    """Generate and save a beep tone."""
    data = generate_sine_wav(frequency, duration_ms, volume)
    save_wav(data, path)
    return path


def generate_silence_file(path: str, duration_ms: int = 1000):
    """Generate and save a silence file."""
    data = generate_silence_wav(duration_ms)
    save_wav(data, path)
    return path


def generate_double_beep_file(path: str, freq: float = 880, beep_ms: int = 150, gap_ms: int = 100, volume: float = 0.4):
    """Generate a double-beep tone (beep-gap-beep) often used as 'recording start' signal."""
    beep1 = generate_sine_wav(freq, beep_ms, volume)
    gap = generate_silence_wav(gap_ms)
    beep2 = generate_sine_wav(freq * 1.2, beep_ms, volume)  # Slightly higher pitch for second beep

    # Concatenate by re-encoding
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_out:
        wav_out.setnchannels(CHANNELS)
        wav_out.setsampwidth(SAMPLE_WIDTH)
        wav_out.setframerate(SAMPLE_RATE)
        for wav_bytes in [beep1, gap, beep2]:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wav_in:
                wav_out.writeframes(wav_in.readframes(wav_in.getnframes()))
    save_wav(buf.getvalue(), path)
    return path


def try_concat_with_pydub(files: list[str], output: str, format_out: str = "mp3") -> bool:
    """Try to concatenate audio files using pydub. Returns False if pydub unavailable."""
    try:
        from pydub import AudioSegment
    except ImportError:
        return False

    combined = AudioSegment.empty()
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext == ".wav":
            seg = AudioSegment.from_wav(f)
        elif ext == ".mp3":
            seg = AudioSegment.from_mp3(f)
        else:
            seg = AudioSegment.from_file(f)
        combined += seg

    combined.export(output, format=format_out)
    return True


def concat_with_ffmpeg(files: list[str], output: str) -> bool:
    """Concatenate audio files using ffmpeg directly."""
    import subprocess
    import tempfile

    # Write file list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for path in files:
            f.write(f"file '{os.path.abspath(path)}'\n")
        list_path = f.name

    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-acodec", "libmp3lame", "-q:a", "2", output],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    finally:
        os.unlink(list_path)


def concat_audio(files: list[str], output: str) -> str:
    """Concatenate audio files. Tries pydub first, then ffmpeg, then fails gracefully."""
    if try_concat_with_pydub(files, output):
        return output
    if concat_with_ffmpeg(files, output):
        return output
    print(f"⚠️  Cannot concatenate audio (need pydub or ffmpeg). Individual files saved.")
    return ""
