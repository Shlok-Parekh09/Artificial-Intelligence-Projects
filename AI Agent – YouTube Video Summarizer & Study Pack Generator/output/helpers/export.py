import os
from helpers.utils import safe_filename, extract_video_id

class ExportAgent:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_markdown(self, url, transcript, summary, flashcards, quiz):
        base_id = extract_video_id(url)
        file_path = os.path.join(
            self.output_dir,
            f"ShikshaAI_Output_{safe_filename(base_id)}.md"
        )

        content = f"""
# 📘 ShikshaAI Study Pack

---

## 📺 URL
{url}

---

## 📝 Summary
{summary}

---

## 🎯 Flashcards
{flashcards}

---

## 🧪 Quiz
{quiz}

---

## 🎤 Transcript (Local Whisper)
{transcript}
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"📄 Exported: {file_path}")
