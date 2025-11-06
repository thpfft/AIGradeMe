# utils/gemini.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to Gemini AI Vision API for grading.

import os
import base64
import requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

def analyze_image(image_path):
    rubric_instructions = """
    Evaluate this hand-drawn floor plan sketch. The rubric:
    1. Sketch of a house floor plan, hand drawn, must include labeled rooms (25%).
    2. Two sentences describing what the sketch represents (25%).
    3. Dimensions of rooms must be present (25%).
    4. Scale indicator showing imperial or metric (10%).
    5. Compass included (10%).
    6. A sentence explaining how this differs from a professional plan (5%).

    For each item:
      - Return True/False if it meets the requirement
      - Extract any relevant text

    At the end:
      - Provide a short explanation (2–4 sentences) describing
        how the submission met or did not meet the rubric requirements.
    """

    # Read image
    with open(image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-1.5-pro:generateContent"
        f"?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": rubric_instructions},
                    {
                        "inline_data": {
                            "mime_type": "image/png",   # adjust if JPEG
                            "data": encoded_image
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "success": False,
            "details": f"Gemini API error ({response.status_code}): {response.text}",
        }
