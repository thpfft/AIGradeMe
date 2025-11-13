# aichecknew.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to AI API for grading

import os
import base64
import requests
import json
import logging
import sys

# Configure logging to output to STDOUT
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    # Explicitly set the handler to stream to stdout for Render compatibility
    handlers=[logging.StreamHandler(sys.stdout)] 
)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

GROK_KEY = os.environ.get("GROK_API_KEY")
if not GROK_KEY:
    raise RuntimeError("GROK_API_KEY not set")

# Load prompt.txt
with open("prompt.txt", "r", encoding="utf-8") as f:
    txt = f.read().strip()

parts = txt.split("\n=== PROMPT ===\n", 1)
if len(parts) != 2:
    raise RuntimeError("prompt.txt must contain '=== PROMPT ===' separator")
RUBRIC_TEXT, PROMPT_TEMPLATE = parts[0].strip(), parts[1].strip()

logging.info("=== PROMPT SENT ===")
logging.info(PROMPT_TEMPLATE)
logging.info("=== END PROMPT ===")

# def analyze_image(image_path: str):
#     with open(image_path, "rb") as f:
#         encoded = base64.b64encode(f.read()).decode("utf-8")
#     ext = os.path.splitext(image_path)[1].lower()
#     mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext.lstrip("."), "application/octet-stream")
#     payload = {
#         "contents": [{"parts": [{"text": PROMPT_TEMPLATE}, {"inline_data": {"mime_type": mime, "data": encoded}}]}]
#     }
# 
#     # url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
#     url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
#     resp = requests.post(url, json=payload)
#     return resp.json() if resp.status_code == 200 else {"success": False, "details": resp.text}

# def analyze_image(image_path: str):
#     logging.info(f"Analyzing image: {image_path}")
#     
#     with open(image_path, "rb") as f:
#         encoded = base64.b64encode(f.read()).decode("utf-8")
#     
#     ext = os.path.splitext(image_path)[1].lower()
#     mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
#         ext.lstrip("."), "application/octet-stream"
#     )
# 
#     # === RAW REQUESTS FOR GROK (OpenAI endpoint) ===
#     headers = {
#         "Authorization": f"Bearer {GROK_KEY}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "model": "grok-3-fast",
#         "messages": [{
#             "role": "user",  # ← String "user" — no enums
#             "content": [
#                 {"type": "text", "text": PROMPT_TEMPLATE},
#                 {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}
#             ]
#         }],
#         "temperature": 0.3,
#         "max_tokens": 400
#     }
#     url = "https://api.x.ai/v1/chat/completions"
# 
#     resp = requests.post(url, json=payload, headers=headers)
#     
#     if resp.status_code == 200:
#         logging.info("Grok response received")
#         content = resp.json()["choices"][0]["message"]["content"]
#         # Return Gemini-compatible structure
#         return {"candidates": [{"content": {"parts": [{"text": content}]}}]}
#     else:
#         error = f"Grok error {resp.status_code}: {resp.text[:200]}"
#         logging.error(error)
#         return {"success": False, "details": error}

def analyze_image(image_path: str):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    ext = os.path.splitext(image_path)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        ext.lstrip("."), "application/octet-stream"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT_TEMPLATE},
                    {"inline_data": {"mime_type": mime, "data": encoded}}
                ]
            }
        ]
    }

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    
    resp = requests.post(url, json=payload)
    
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Gemini error {resp.status_code}: {resp.text[:200]}")
        return {"success": False, "details": resp.text}

def get_rubric() -> str:
    return RUBRIC_TEXT
