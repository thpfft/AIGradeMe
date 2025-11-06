# utils/gemini.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Handles calls to Gemini AI Vision API for grading.

import os
import base64
import requests
import json

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY is None:
    raise RuntimeError("Error: GEMINI_API_KEY not set in environment")

def analyze_image(image_path):
    # Sends the uploaded image to Gemini AI for grading according to the rubric.
    # Returns structured JSON including scores and feedback.
    
    # Rubric instructions for AI
    rubric_instructions = """
Evaluate this hand-drawn floor plan sketch according to the rubric:
1. Sketch of a house floor plan, hand drawn, must include labeled rooms (25%).
2. Two sentences describing what the sketch represents (25%).
3. Dimensions of rooms must be present (25%).
4. Scale indicator showing imperial or metric (10%).
5. Compass included (10%).
6. A sentence explaining how this differs from a professional plan (5%).

Please return JSON with the following fields:
{
  "scores": {
    "sketch": int,
    "description": int,
    "dimensions": int,
    "scale": int,
    "compass": int,
    "differences": int
  },
  "feedback": str
}

- Scores should reflect the AI judgment: full points if requirement met, partial if partially met, zero if not included.
- In making the judgement, don't be too strict (be generous, just looking for more serious failures); 100% is very possible
- Provide a short textual explanation in "feedback" (2–4 sentences).
- Output must be valid JSON only, no extra commentary.
"""

    # Encode image to base64
    with open(image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash-lite:generateContent"
        f"?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": rubric_instructions},
                    {
                        "inline_data": {
                            "mime_type": "application/octet-stream",  # should work for any file type
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
