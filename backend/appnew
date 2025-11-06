# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Flask backend for grading hand-drawn floor plan sketches.

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from utils import gemini  # Your existing gemini.analyze_image function
import os
import tempfile
import re
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow frontend from any origin (adjust in production if needed)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_json_from_markdown(text):
    """Extract and parse JSON from Gemini's possible markdown-wrapped response."""
    if not text:
        return None
    
    # Remove ```json ... ``` blocks
    cleaned = re.sub(r"^```json\s*|```$", "", text.strip(), flags=re.MULTILINE)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from Gemini response: {e}")
        logger.debug(f"Raw text was: {cleaned}")
        return {"raw_feedback": cleaned}

@app.route("/submit", methods=["POST"])
def submit():
    try:
        # Check required fields
        if "name" not in request.form or "email" not in request.form:
            return jsonify({"success": False, "error": "Name and email are required."}), 400
        
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded."}), 400
        
        image = request.files["image"]
        if image.filename == '':
            return jsonify({"success": False, "error": "No file selected."}), 400
        
        if not allowed_file(image.filename):
            return jsonify({"success": False, "error": "Invalid file type."}), 400

        name = request.form["name"].strip()
        email = request.form["email"].strip()

        # Save uploaded image temporarily
        filename = secure_filename(image.filename)
        suffix = os.path.splitext(filename)[1].lower() or '.jpg'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            image.save(temp_path)

        try:
            # Analyze with Gemini
            logger.info(f"Analyzing image for {name} ({email})")
            analysis = gemini.analyze_image(temp_path)
            
            # Extract text from Gemini response
            raw_text = None
            candidates = analysis.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    raw_text = parts[0].get("text", "")

            if not raw_text:
                raw_text = str(analysis)

            # Parse structured feedback
            structured = extract_json_from_markdown(raw_text)
            
            if isinstance(structured, dict) and "scores" in structured:
                # Success: clean structured response
                response = {
                    "success": True,
                    "name": name,
                    "email": email,
                    "scores": structured.get("scores", {}),
                    "feedback": structured.get("feedback", "No detailed feedback provided.").strip(),
                }
            else:
                # Fallback: return raw text
                response = {
                    "success": True,
                    "name": name,
                    "email": email,
                    "scores": {},
                    "feedback": raw_text.strip() or "No feedback generated.",
                    "warning": "Could not parse structured scores. Raw output attached."
                }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}")
            return jsonify({
                "success": False,
                "name": name,
                "email": email,
                "error": "Failed to analyze image. Please try again."
            }), 500

        finally:
            # Always clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    except Exception as e:
        logger.error(f"Unexpected error in /submit: {e}")
        return jsonify({"success": False, "error": "Internal server error."}), 500


@app.route("/test", methods=["GET"])
def test():
    """Simple health check + mock response"""
    return jsonify({
        "success": True,
        "message": "Server is running!",
        "test_scores": {
            "sketch": 20, "description": 22, "dimensions": 18,
            "scale": 10, "compass": 8, "differences": 7
        },
        "feedback": "This is a test response. Your server works!"
    })


@app.route("/", methods=["GET"])
def home():
    return "Sketch grader backend is live! Use /submit (POST) or /test (GET)"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
