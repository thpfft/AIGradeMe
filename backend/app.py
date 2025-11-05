# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Flask backend for grading hand-drawn floor plan sketches. Receives submissions and returns grading results (placeholder).

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/submit", methods=["POST"])
def submit():
    # Placeholder endpoint for testing
    return jsonify({"message": "Backend is functional."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
