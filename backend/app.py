# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Flask backend for grading hand-drawn floor plan sketches.

from flask import Flask, request, jsonify
from utils import gemini, grade
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route("/submit", methods=["POST"])
def submit():
    # Receives submission with name, email, image file (sketch)
    # Returns grading results as JSON

    data = request.form
    image = request.files.get("image")

    if image:
        # Save the uploaded image to a temporary file
        filename = secure_filename(image.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            temp_path = tmp.name
            image.save(temp_path)

        # Send temp file to Gemini
        analysis = gemini.analyze_image(temp_path)

        # Delete the temp file after sending
        try:
            os.remove(temp_path)
        except Exception:
            pass
    else:
        analysis = {"success": False, "details": "No image uploaded."}

    # Build submission dict for grading
    submission_data = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "analysis": analysis
    }

    # Extract scores and feedback directly from Gemini
    scores = {
        "sketch": None,
        "description": None,
        "dimensions": None,
        "scale": None,
        "compass": None,
        "differences": None,
    }
    feedback = "(No feedback from Gemini.)"

    try:
        # Gemini's response contains candidates -> content -> parts -> text
        raw_text = analysis["candidates"][0]["content"]["parts"][0]["text"]
    
        # Remove any ```json ``` wrappers
        raw_text = raw_text.strip("```json").strip("```").strip()
    
        gemini_result = json.loads(raw_text)
        scores.update(gemini_result.get("scores", {}))
        feedback = gemini_result.get("feedback", feedback)
    except Exception:
        pass

    # Compute total (sum numeric scores)
    total = sum(v for v in scores.values() if isinstance(v, (int, float)))

    # Build final result
    results = {
        "name": submission_data.get("name", ""),
        "email": submission_data.get("email", ""),
        "scores": scores,
        "total": total,
        "feedback": feedback,
    }

    return jsonify(results)
       
    
    # Get grading results
    # results = grade.grade_submission(submission_data)

    # Return JSON response
    # return jsonify(results)

    # Test: Instead of grading, just return Gemini output
    # return jsonify({
    #     "name": submission_data.get("name", ""),
    #     "email": submission_data.get("email", ""),
    #     "gemini_raw": analysis
    # })

# # Test Only

@app.route("/test", methods=["GET"])
def test_submission():
    # Hardcoded test submission data
    submission_data = {
        "name": "Ron Geee",
        "email": "ron@example.com",
        "analysis": {
            "success": True,
            "details": "Simulated image analysis placeholder"
        }
    }

    # Use your existing grade function
    results = grade.grade_submission(submission_data)

    # Return as JSON
    return jsonify(results)

# # 

if __name__ == "__main__":
    # Run Flask server
    app.run(host="0.0.0.0", port=5000)
