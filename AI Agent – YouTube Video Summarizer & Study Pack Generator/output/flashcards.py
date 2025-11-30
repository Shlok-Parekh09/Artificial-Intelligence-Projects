def generate_flashcards(summary: str) -> str:
    if not GROQ_KEY: return "⚠️ GROQ_KEY missing."
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content":
                       f"Generate 15 Q&A flashcards from this summary. Format: Q: ... A: ...\n\n{summary}"}],
            temperature=0.4,
            max_tokens=1200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"
