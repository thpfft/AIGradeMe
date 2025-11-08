# utils/gemini.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to Gemini AI Vision API for grading.

import os
import base64
import requests
import json

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

# Load prompt.txt from same directory
with open("prompt.txt", "r", encoding="utf-8") as f:
    txt = f.read().strip()

parts = txt.split("\n=== PROMPT ===\n", 1)
if len(parts) != 2:
    raise RuntimeError("prompt.txt must contain '=== PROMPT ===' separator")
RUBRIC_TEXT, PROMPT_TEMPLATE = parts[0].strip(), parts[1].strip()

print("=== PROMPT SENT TO GEMINI ===")
print(PROMPT_TEMPLATE)
print("=== END PROMPT ===")

def analyze_image(image_path: str):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext.lstrip("."), "application/octet-stream")
    payload = {
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE}, {"inline_data": {"mime_type": mime, "data": encoded}}]}]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    resp = requests.post(url, json=payload)
    return resp.json() if resp.status_code == 200 else {"success": False, "details": resp.text}

def get_rubric() -> str:
    return RUBRIC_TEXT
