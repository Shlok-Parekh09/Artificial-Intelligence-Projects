from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests
import yaml

try:  # ffmpeg-python wraps the ffmpeg CLI
    import ffmpeg  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency check
    raise RuntimeError("ffmpeg-python is not installed. Run 'pip install ffmpeg-python'.") from exc

try:
    import whisper  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency check
    raise RuntimeError("openai-whisper is not installed. Run 'pip install openai-whisper'.") from exc

try:  # Groq compatibility uses the OpenAI SDK surface
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

try:
    from mistralai import Mistral
except ImportError:  # pragma: no cover - optional dependency
    Mistral = None  # type: ignore

try:
    from kaggle_secrets import UserSecretsClient  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    UserSecretsClient = None  # type: ignore


warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("shikshaai")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
DEFAULT_CONFIG = """output_dir: "./output"
max_workers: 1
chunk_length: 600
cookies_file: ""
video_ids: "UdE-W30oOXo"
"""


def ensure_config() -> None:
    if os.path.exists(CONFIG_PATH):
        return
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        handle.write(DEFAULT_CONFIG)
    logger.info("Created default config at %s", CONFIG_PATH)


def load_config() -> dict:
    ensure_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("config.yaml must contain a mapping")
    os.makedirs(data.get("output_dir", "./output"), exist_ok=True)
    return data


CONFIG = load_config()
TEMP_COOKIES_PATH: Optional[str] = None


def resolve_secrets() -> dict:
    secrets = {
        "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
    }
    missing = [key for key, value in secrets.items() if not value]
    if missing and UserSecretsClient is not None:
        try:
            client = UserSecretsClient()
            for key in missing:
                if secrets[key]:
                    continue
                try:
                    secrets[key] = client.get_secret(key)
                except Exception as err:  # pragma: no cover - Kaggle specific
                    logger.warning("Could not read Kaggle secret %s: %s", key, err)
        except Exception as err:  # pragma: no cover - Kaggle specific
            logger.warning("Kaggle secrets unavailable: %s", err)
    return secrets


SECRETS = resolve_secrets()
APIFY_KEY = SECRETS.get("APIFY_API_KEY")
GROQ_KEY = SECRETS.get("GROQ_API_KEY")
MISTRAL_KEY = SECRETS.get("MISTRAL_API_KEY")

groq_client: Optional[OpenAI] = None  # type: ignore
mistral_client: Optional[Mistral] = None  # type: ignore

if GROQ_KEY:
    if OpenAI is None:
        raise RuntimeError("The 'openai' package is required for Groq support. Install it via 'pip install openai'.")
    groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY)
else:
    logger.warning("GROQ_API_KEY is not set; flashcard generation will be disabled.")

if MISTRAL_KEY:
    if Mistral is None:
        raise RuntimeError("The 'mistralai' package is required for Mistral support. Install it via 'pip install mistralai'.")
    mistral_client = Mistral(api_key=MISTRAL_KEY)
else:
    logger.warning("MISTRAL_API_KEY is not set; quiz generation will be disabled.")

if not APIFY_KEY:
    logger.warning("APIFY_API_KEY is not set; the APIfy summariser fallback will be skipped.")


def extract_video_id(url: str) -> str:
    match = re.search(r"(?:youtu\.be/|v=)([A-Za-z0-9_-]{6,})", url)
    return match.group(1) if match else "video"


def safe_filename(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in text)


def get_audio_duration(file_path: str) -> float:
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe["format"]["duration"])
    except ffmpeg.Error as err:
        detail = err.stderr.decode() if err.stderr else str(err)
        logger.error("ffmpeg probe failed: %s", detail)
        return 0.0


def split_audio(input_file: str, chunk_length: int = 600) -> None:
    if os.path.exists("chunks"):
        shutil.rmtree("chunks")
    os.makedirs("chunks", exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-f",
        "segment",
        "-segment_time",
        str(chunk_length),
        "-c",
        "copy",
        os.path.join("chunks", "out%03d.mp3"),
    ]
    subprocess.run(cmd, check=True)


def choose_whisper_model(duration_seconds: float) -> str:
    if duration_seconds < 600:
        return "base"
    if duration_seconds < 3600:
        return "small"
    return "medium"


class TranscriptAgent:
    def __init__(self, chunk_length: int) -> None:
        self.chunk_length = chunk_length

    def download_audio(self, url: str, out_path: str) -> None:
        logger.info("Downloading audio with yt-dlp...")
        cookies_file = CONFIG.get("cookies_file", "").strip()
        cmd = ["yt-dlp", "--no-warnings"]
        if cookies_file:
            cmd += ["--cookies", cookies_file]
        cmd += ["-f", "bestaudio/best", "-x", "--audio-format", "mp3", "-o", out_path, url]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            logger.warning("bestaudio failed; retrying with fallback format")
            fallback_cmd = ["yt-dlp", "--no-warnings"]
            if cookies_file:
                fallback_cmd += ["--cookies", cookies_file]
            fallback_cmd += ["-f", "best", "-x", "--audio-format", "mp3", "-o", out_path, url]
            subprocess.run(fallback_cmd, check=True)

    def transcribe(self, url: str) -> str:
        video_id = extract_video_id(url)
        audio_file = f"temp_{video_id}.mp3"
        if os.path.exists(audio_file):
            os.remove(audio_file)
        self.download_audio(url, audio_file)
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        duration = get_audio_duration(audio_file)
        model_name = choose_whisper_model(duration)
        logger.info("Loading Whisper model: %s", model_name)
        model = whisper.load_model(model_name)
        if duration <= self.chunk_length:
            result = model.transcribe(audio_file)
            return result["text"].strip()
        split_audio(audio_file, self.chunk_length)
        transcript_parts = []
        for chunk_file in sorted([item for item in os.listdir("chunks") if item.endswith(".mp3")]):
            path = os.path.join("chunks", chunk_file)
            result = model.transcribe(path)
            transcript_parts.append(result["text"])
        return "\n".join(transcript_parts).strip()


def summarize_with_apify(transcript: str) -> Optional[str]:
    if not APIFY_KEY:
        return None
    url = "https://api.apify.com/v2/acts/easyapi/text-summarization/run-sync"
    payload = {"text": transcript, "output_sentences": 5}
    headers = {"Authorization": f"Bearer {APIFY_KEY}"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        if response.status_code != 200:
            logger.warning("APIfy summary failed with status %s", response.status_code)
            return None
        data = response.json()
        output = data.get("output", [])
        if isinstance(output, list) and output:
            collected = " ".join(item.get("text", "") for item in output if isinstance(item, dict))
            return collected.strip() or None
        summary = data.get("summary") or data.get("output", {}).get("summary", "")
        return summary.strip() or None
    except Exception as err:
        logger.warning("APIfy error: %s", err)
        return None


def summarize_with_groq(transcript: str) -> Optional[str]:
    if not groq_client:
        return None
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this lecture transcript into a clear outline:\n\n{transcript[:15000]}",
                }
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as err:
        logger.warning("Groq error: %s", err)
        return None


def summarize_with_mistral(transcript: str) -> Optional[str]:
    if not mistral_client:
        return None
    try:
        response = mistral_client.chat.complete(
            model="mistral-small-2409",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this lecture transcript into structured notes:\n\n{transcript[:15000]}",
                }
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as err:
        logger.warning("Mistral error: %s", err)
        return None


def generate_summary(transcript: str) -> str:
    for provider in (summarize_with_apify, summarize_with_groq, summarize_with_mistral):
        summary = provider(transcript)
        if summary:
            return summary
    raise RuntimeError("All summarisation providers failed. Ensure API keys are configured correctly.")


def generate_flashcards(summary: str) -> str:
    if not groq_client:
        return "⚠️ GROQ_API_KEY missing."
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": "Generate 15 Q&A flashcards from this summary. Format: Q: ... A: ...\n\n" + summary,
                }
            ],
            temperature=0.4,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as err:
        return f"Error: {err}"


def generate_quiz(summary: str) -> str:
    if not mistral_client:
        return "⚠️ MISTRAL_API_KEY missing."
    try:
        response = mistral_client.chat.complete(
            model="mistral-small-2409",
            messages=[
                {
                    "role": "user",
                    "content": "Create a 10-question MCQ quiz with answers and rationales based on:\n" + summary,
                }
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    except Exception as err:
        return f"Error: {err}"


class ExportAgent:
    def save_markdown(self, url: str, transcript: str, summary: str, flashcards: str, quiz: str) -> None:
        markdown = (
            "# 📘 ShikshaAI Study Pack\n" "---\n" "## 📺 URL\n" f"{url}\n" "---\n" "## 📝 Summary\n" f"{summary}\n" "---\n" "## 🎯 Flashcards\n" f"{flashcards}\n" "---\n" "## 🧪 Quiz\n" f"{quiz}\n" "---\n" "## 🎤 Transcript (Local Whisper)\n" f"{transcript}\n"
        )
        base_id = extract_video_id(url)
        output_file = os.path.join(CONFIG["output_dir"], f"ShikshaAI_Output_{safe_filename(base_id)}.md")
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        logger.info("Exported study pack -> %s", output_file)


def process_url(url: str) -> None:
    logger.info("===== Processing: %s =====", url)
    transcriber = TranscriptAgent(CONFIG.get("chunk_length", 600))
    exporter = ExportAgent()
    transcript = transcriber.transcribe(url)
    summary = generate_summary(transcript)
    flashcards = generate_flashcards(summary)
    quiz = generate_quiz(summary)
    exporter.save_markdown(url, transcript, summary, flashcards, quiz)
    logger.info("Finished: %s", url)


def input_urls() -> list[str]:
    ids_raw = CONFIG.get("video_ids", "")
    urls = [f"https://youtu.be/{item.strip()}" for item in ids_raw.split(",") if item.strip()]
    if not urls:
        raise ValueError("No video IDs configured in config.yaml")
    return urls


def setup_cookies() -> None:
    global TEMP_COOKIES_PATH
    configured = CONFIG.get("cookies_file", "").strip()
    if configured:
        if os.path.exists(configured):
            logger.info("Using cookies from %s", configured)
            return
        logger.warning("Configured cookies file %s does not exist; ignoring.", configured)
        CONFIG["cookies_file"] = ""
    kaggle_input_root = "/kaggle/input"
    if os.path.exists(kaggle_input_root):  # Kaggle notebook flow
        for root, _, files in os.walk(kaggle_input_root):
            if "cookies.txt" in files:
                src = os.path.join(root, "cookies.txt")
                dst = "/kaggle/working/cookies.txt"
                shutil.copy(src, dst)
                CONFIG["cookies_file"] = dst
                TEMP_COOKIES_PATH = dst
                logger.info("Copied cookies to %s", dst)
                return
        logger.warning("No cookies.txt found under %s", kaggle_input_root)
    else:  # local convenience
        local_candidate = os.path.join(os.path.dirname(__file__), "cookies.txt")
        if os.path.exists(local_candidate):
            CONFIG["cookies_file"] = local_candidate
            logger.info("Detected local cookies at %s", local_candidate)
        else:
            logger.info("No cookies configured; continuing without authenticated yt-dlp.")


def cleanup_cookies() -> None:
    if TEMP_COOKIES_PATH and os.path.exists(TEMP_COOKIES_PATH):
        os.remove(TEMP_COOKIES_PATH)
        logger.info("Removed temporary cookies file %s", TEMP_COOKIES_PATH)


def main() -> None:
    setup_cookies()
    urls = input_urls()
    max_workers = max(1, int(CONFIG.get("max_workers", 1)))
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_url, urls)
    finally:
        cleanup_cookies()


if __name__ == "__main__":
    main()
