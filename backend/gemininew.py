# utils/gemini.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to Gemini AI Vision API for grading.

import os
import base64
import requests
import json
import logging
import sys
from xai_sdk import Client

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

logging.info("=== PROMPT SENT TO GEMINI ===")
logging.info(PROMPT_TEMPLATE)
logging.info("=== END PROMPT ===")

# === xAI Client ===
client = Client(api_key=GROK_KEY)

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

def analyze_image(image_path: str):
    logging.info(f"Analyzing image: {image_path}")
    
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    ext = os.path.splitext(image_path)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        ext.lstrip("."), "application/octet-stream"
    )

    try:
        # === xAI SDK Call ===
        response = client.chat.create(model="grok-4-0709")  # Grok-4 (multimodal)
        response.append_user_message(PROMPT_TEMPLATE)
        response.append_user_image(f"data:{mime};base64,{encoded}")
        response = response.sample()

        content = response.content
        logging.info("Grok response received")
        
        # Return Gemini-compatible structure
        return {"candidates": [{"content": {"parts": [{"text": content}]}}]}

    except Exception as e:
        error_msg = f"Grok API error: {str(e)}"
        logging.error(error_msg)
        return {"success": False, "details": error_msg}

def get_rubric() -> str:
    return RUBRIC_TEXT
