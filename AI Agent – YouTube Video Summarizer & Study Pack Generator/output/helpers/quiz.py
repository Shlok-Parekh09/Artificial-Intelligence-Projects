def generate_quiz(summary: str) -> str:
    if not MISTRAL_KEY: return "⚠️ MISTRAL_KEY missing."
    try:
        resp = mistral_client.chat.complete(
            model="mistral-small-2409",
            messages=[{"role": "user", "content":
                       f"Create a 10-question MCQ quiz with answers and rationales based on:\n{summary}"}],
            temperature=0.4,
            max_tokens=1500
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"
