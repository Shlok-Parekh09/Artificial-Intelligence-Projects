import requests
import logging
from helpers.utils import extract_video_id

logger = logging.getLogger("shikshaai")

def summarize_with_apify(api_key, transcript):
    if not api_key:
        return None

    url = "https://api.apify.com/v2/acts/easyapi/text-summarization/run-sync"
    payload = {"text": transcript, "output_sentences": 5}
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            output = data.get("output", [])
            if isinstance(output, list):
                return " ".join([o.get("text", "") for o in output]).strip()
            return data.get("summary", "").strip()
    except Exception as e:
        logger.warning(f"APIfy error: {e}")
    return None


def summarize_with_groq(client, transcript):
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"Summarize into a clear outline:\n\n{transcript[:15000]}"
            }],
            temperature=0.3, max_tokens=1000
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq error: {e}")
        return None


def summarize_with_mistral(client, transcript):
    if client is None:
        return None
    try:
        resp = client.chat.complete(
            model="mistral-small-2409",
            messages=[{
                "role": "user",
                "content": f"Summarize into structured notes:\n\n{transcript[:15000]}"
            }],
            temperature=0.3, max_tokens=1200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Mistral error: {e}")
        return None


def generate_summary(transcript, apify_key, groq_client, mistral_client):
    summary = summarize_with_apify(apify_key, transcript)
    if summary: return summary

    summary = summarize_with_groq(groq_client, transcript)
    if summary: return summary

    summary = summarize_with_mistral(mistral_client, transcript)
    if summary: return summary

    raise RuntimeError("All summarizers failed.")
