import os
import re
import ffmpeg
import subprocess
import logging

logger = logging.getLogger("shikshaai")

# -------------------------
# Utility Functions
# -------------------------

def extract_video_id(url: str) -> str:
    m = re.search(r"(?:youtu\.be/|v=)([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else "video"

def safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)

def get_audio_duration(file_path: str) -> float:
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe["format"]["duration"])
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg probe failed: {e.stderr.decode() if e.stderr else str(e)}")
        return 0.0

def split_audio(input_file: str, chunk_length: int = 600):
    if os.path.exists("chunks"):
        import shutil
        shutil.rmtree("chunks")

    os.makedirs("chunks", exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-f", "segment", "-segment_time", str(chunk_length),
        "-c", "copy", "chunks/out%03d.mp3"
    ]
    subprocess.run(cmd, check=True)

def choose_whisper_model(duration: float) -> str:
    if duration < 600:
        return "base"
    elif duration < 3600:
        return "small"
    else:
        return "medium"
