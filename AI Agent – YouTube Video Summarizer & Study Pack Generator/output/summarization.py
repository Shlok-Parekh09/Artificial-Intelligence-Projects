def summarize_with_apify(transcript: str) -> Optional[str]:
    if not APIFY_KEY: return None
    url = "https://api.apify.com/v2/acts/easyapi/text-summarization/run-sync"
    payload = {"text": transcript, "output_sentences": 5}
    headers = {"Authorization": f"Bearer {APIFY_KEY}"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            output = data.get("output", [])
            if isinstance(output, list) and len(output) > 0:
                summary = " ".join([item.get("text", "") for item in output if isinstance(item, dict)])
                return summary.strip() if summary else None
            summary = data.get("summary") or data.get("output", {}).get("summary", "")
            return summary.strip() if summary else None
    except Exception as e:
        logger.warning(f"APIfy error: {e}")
    return None
def summarize_with_groq(transcript: str) -> Optional[str]:
    if not GROQ_KEY: return None
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Summarize this lecture transcript into a clear outline:\n\n{transcript[:15000]}"}],
            temperature=0.3,
            max_tokens=1000
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq error: {e}")
        return None
def summarize_with_mistral(transcript: str) -> Optional[str]:
    if not MISTRAL_KEY: return None
    try:
        resp = mistral_client.chat.complete(
            model="mistral-small-2409",
            messages=[{"role": "user", "content": f"Summarize this lecture transcript into structured notes:\n\n{transcript[:15000]}"}],
            temperature=0.3,
            max_tokens=1200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Mistral error: {e}")
        return None
def generate_summary(transcript: str) -> str:
    # Try providers in order
    summary = summarize_with_apify(transcript)
    if summary: return summary
   
    summary = summarize_with_groq(transcript)
    if summary: return summary
       
    summary = summarize_with_mistral(transcript)
    if summary: return summary
       
    raise RuntimeError("All summarization providers failed.")
