# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Flask backend for grading hand-drawn floor plan sketches.

from flask import Flask, request, jsonify
from utils import gemini, grade

app = Flask(__name__)

@app.route("/submit", methods=["POST"])
def submit():
    # Receives submission with: name, email, image file (sketch)
    # Returns grading results as JSON

    data = request.form
    image = request.files.get("image")

    # For now, simulate sending to Gemini
    if image:
        analysis = gemini.analyze_image(image.filename)
    else:
        analysis = {"success": False, "details": "No image uploaded!"}

    # Build submission dict for grading
    submission_data = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "analysis": analysis
    }

    # Get grading results
    results = grade.grade_submission(submission_data)

    # Return JSON response
    return jsonify(results)

if __name__ == "__main__":
    # Run Flask server
    app.run(host="0.0.0.0", port=5000)


@app.route("/test", methods=["GET"])
def test_submission():
    # Hardcoded submission data for testing
    submission_data = {
        "name": "GG",
        "email": "G@example.com",
        "analysis": {
            "success": True,
            "details": "Simulated image analysis placeholder"
        }
    }

    # Run the placeholder grading
    results = grade.grade_submission(submission_data)

    # Return results as JSON
    return results
