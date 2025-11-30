# -------------------------
# Export
# -------------------------
class ExportAgent:
    def save_markdown(self, url: str, transcript: str, summary: str, flashcards: str, quiz: str):
        md = f"""# 📘 ShikshaAI Study Pack
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
        base_id = extract_video_id(url)
        output_file = os.path.join(config["output_dir"], f"ShikshaAI_Output_{safe_filename(base_id)}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)
        logger.info(f"📄 Exported: {output_file}")
