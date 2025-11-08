# utils/gemini.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to Gemini AI Vision API for grading.

# utils/gemini.py
import os
import base64
import requests
import json

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

# ----------------------------------------------------------------------
# Load prompt.txt (must be in the same folder as this file)
# ----------------------------------------------------------------------
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "prompt.txt")
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    txt = f.read().strip()

# Split on the first blank line that follows a line containing "=== PROMPT ==="
# Anything before is the rubric, anything after is the real prompt.
parts = txt.split("\n=== PROMPT ===\n", 1)
if len(parts) != 2:
    raise RuntimeError("prompt.txt must contain exactly one '=== PROMPT ===' separator")

RUBRIC_TEXT, PROMPT_TEMPLATE = parts[0].strip(), parts[1].strip()


def analyze_image(image_path: str):
    """
    Sends the image to Gemini and returns the raw Gemini JSON.
    The caller (appnew.py) will parse the JSON into scores/feedback.
    """
    # Encode image
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    # MIME type
    ext = os.path.splitext(image_path)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        ext.lstrip("."), "application/octet-stream"
    )

    # Build payload – the prompt is the *template* from prompt.txt
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT_TEMPLATE},
                    {"inline_data": {"mime_type": mime, "data": encoded}},
                ]
            }
        ]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload)

    if resp.status_code == 200:
        return resp.json()
    else:
        return {
            "success": False,
            "details": f"Gemini error {resp.status_code}: {resp.text}",
        }


def get_rubric() -> str:
    """Return the rubric text for display in the UI."""
    return RUBRIC_TEXT
