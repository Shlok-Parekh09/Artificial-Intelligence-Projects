import json
from helpers.utils import ensure_dir

def save_summary(text, path="output/summary.txt"):
    ensure_dir("output")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def save_flashcards(text, path="output/flashcards.txt"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def save_quiz(text, path="output/quiz.txt"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def save_json(data, path="output/data.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
