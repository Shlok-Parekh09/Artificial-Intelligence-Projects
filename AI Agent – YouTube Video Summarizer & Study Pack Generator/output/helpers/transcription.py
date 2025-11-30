class TranscriptAgent:
    def __init__(self, chunk_length: int):
        self.chunk_length = chunk_length

    def download_audio(self, url: str, out_path: str):
        logger.info("Downloading audio with yt-dlp...")
        cookies_file = config.get("cookies_file", "").strip()
        cmd = [
            "yt-dlp", "--no-warnings", "--cookies", cookies_file,
            "-f", "bestaudio/best", "-x", "--audio-format", "mp3",
            "-o", out_path, url
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            logger.warning("⚠️ bestaudio failed, retrying with fallback format...")
            fallback_cmd = [
                "yt-dlp", "--no-warnings", "--cookies", cookies_file,
                "-f", "best", "-x", "--audio-format", "mp3",
                "-o", out_path, url
            ]
            subprocess.run(fallback_cmd, check=True)

    def transcribe(self, url: str) -> str:
        vid = extract_video_id(url)
        audio_file = f"temp_{vid}.mp3"
        if os.path.exists(audio_file):
            os.remove(audio_file)

        self.download_audio(url, audio_file)

        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        duration = get_audio_duration(audio_file)
        model_name = choose_whisper_model(duration)
        logger.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)

        if duration <= self.chunk_length:
            result = model.transcribe(audio_file)
            return result["text"].strip()

        split_audio(audio_file, self.chunk_length)
        transcript_parts = []
        for chunk in sorted([c for c in os.listdir("chunks") if c.endswith(".mp3")]):
            result = model.transcribe(os.path.join("chunks", chunk))
            transcript_parts.append(result["text"])
        return "\n".join(transcript_parts).strip()

