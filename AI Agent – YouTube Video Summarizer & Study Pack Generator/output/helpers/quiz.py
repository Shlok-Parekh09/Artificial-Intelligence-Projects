def generate_quiz(summary: str, mistral_client):
    if mistral_client is None:
        return "⚠️ MISTRAL_KEY missing."
    try:
        resp = mistral_client.chat.complete(
            model="mistral-small-2409",
            messages=[{
                "role": "user",
                "content": f"Create a 10-question MCQ quiz with answers:\n{summary}"
            }],
            temperature=0.4, max_tokens=1500
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"
