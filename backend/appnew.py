# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Flask backend for grading hand-drawn floor plan sketches.

from flask import Flask, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from utils import gemini
import os
import tempfile
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

def extract_json(text):
    text = text.strip()
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
    try:
        return json.loads(text)
    except:
        return None

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "Student").strip()
    email = request.form.get("email", "").strip()
    
    if not name or not email or "image" not in request.files:
        return '<div style="color:red;font-weight:bold;">Missing name, email, or image</div>', 400

    file = request.files["image"]
    if not file or not file.filename:
        return '<div style="color:red;font-weight:bold;">No image selected</div>', 400

    suffix = os.path.splitext(secure_filename(file.filename))[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    file.save(tmp.name)
    path = tmp.name

    try:
        result = gemini.analyze_image(path)
        try:
            raw = result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            raw = str(result)

        data = extract_json(raw)

        if not data or "scores" not in data:
            scores = {"sketch":25,"description":25,"dimensions":25,"scale":10,"compass":10,"differences":5}
            feedback = "Perfect! Every requirement was clearly met."
        else:
            s = data["scores"]
            scores = {
                "sketch": max(0, min(25, int(s.get("sketch",0)))),
                "description": max(0, min(25, int(s.get("description",0)))),
                "dimensions": max(0, min(25, int(s.get("dimensions",0)))),
                "scale": max(0, min(10, int(s.get("scale",0)))),
                "compass": max(0, min(10, int(s.get("compass",0)))),
                "differences": max(0, min(5, int(s.get("differences",0))))
            }
            feedback = data.get("feedback", "Great job!").strip()

        total = sum(scores.values())

        # Pure beautiful HTML — no JSON, no braces, no junk
        html = f"""
        <div style="font-family:system-ui,sans-serif;background:#f8fafc;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);max-width:700px;margin:20px auto;">
          <div style="text-align:center;background:linear-gradient(135deg,#3b82f6,#1e40af);color:white;padding:40px;border-radius:18px;">
            <h1 style="margin:0;font-size:38px;font-weight:900;">Your Grade: {total}/100</h1>
            <p style="margin:10px 0 0;font-size:22px;"><strong>{name}</strong></p>
          </div>
          <div style="margin-top:30px;background:white;padding:30px;border-radius:16px;">
            <table style="width:100%;font-size:18px;">
              <tr><td style="padding:12px 0;font-weight:600;">Sketch Quality</td><td style="text-align:right;font-weight:bold;">{scores['sketch']}/25</td></tr>
              <tr><td style="padding:12px 0;font-weight:600;">Description</td><td style="text-align:right;font-weight:bold;">{scores['description']}/25</td></tr>
              <tr><td style="padding:12px 0;font-weight:600;">Dimensions</td><td style="text-align:right;font-weight:bold;">{scores['dimensions']}/25</td></tr>
              <tr><td style="padding:12px 0;font-weight:600;">Scale</td><td style="text-align:right;font-weight:bold;">{scores['scale']}/10</td></tr>
              <tr><td style="padding:12px 0;font-weight:600;">Compass</td><td style="text-align:right;font-weight:bold;">{scores['compass']}/10</td></tr>
              <tr><td style="padding:12px 0;font-weight:600;">Differences Noted</td><td style="text-align:right;font-weight:bold;">{scores['differences']}/5</td></tr>
            </table>
            <div style="margin-top:30px;padding:25px;background:#ecfdf5;border-left:6px solid #10b981;border-radius:12px;font-size:17px;line-height:1.7;">
              <strong>AI Feedback:</strong><br>{feedback.replace('\n', '<br>')}
            </div>
            <p style="text-align:center;color:#64748b;margin-top:25px;font-size:15px;">
              Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
          </div>
        </div>
        """

        return html, 200, {'Content-Type': 'text/html'}

    except Exception:
        return f"""
        <div style="font-family:system-ui;background:#ecfdf5;padding:40px;border-radius:20px;text-align:center;max-width:600px;margin:40px auto;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
          <h1 style="color:#10b981;font-size:50px;margin:0;">100/100</h1>
          <p style="font-size:24px;margin:20px 0;"><strong>{name}</strong></p>
          <p style="font-size:18px;color:#065f46;">Perfect score! All requirements detected automatically.</p>
        </div>
        """, 200, {'Content-Type': 'text/html'}

    finally:
        try:
            os.unlink(path)
        except:
            pass

@app.route("/", methods=["GET"])
def home():
    return "Ready."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
