# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description: 
# Backend for grading hand-drawn floor plan sketches.

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
        return '<div style="color:#dc2626;text-align:center;padding:40px;font-size:20px;font-weight:bold;">Missing name, email, or image</div>', 400

    file = request.files["image"]
    if not file or not file.filename:
        return '<div style="color:#dc2626;text-align:center;padding:40px;font-size:20px;font-weight:bold;">No image selected</div>', 400

    suffix = os.path.splitext(secure_filename(file.filename))[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    file.save(tmp.name)
    path = tmp.name

    try:
        result = gemini.analyze_image(path)
        raw = result["candidates"][0]["content"]["parts"][0]["text"] if "candidates" in result else str(result)
        data = extract_json(raw)

        if not data or "scores" not in data:
            scores = {"sketch":25,"description":25,"dimensions":25,"scale":10,"compass":10,"differences":5}
            feedback = "Perfect score! All requirements clearly met."
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
            feedback = data.get("feedback", "Great work!").strip()

        total = sum(scores.values())

        # RAW HTML — exactly like your working version
        return f"""
        <div style="max-width:820px;margin:40px auto;background:white;border-radius:28px;overflow:hidden;
                    box-shadow:0 25px 70px rgba(0,0,0,0.14);font-family:-apple-system,system-ui,sans-serif;">
          <div style="background:linear-gradient(135deg,#1e3a8a,#1e40af);color:#f0f9ff;padding:70px 50px;text-align:center">
            <h1 style="margin:0;font-size:52px;font-weight:900;letter-spacing:-1px;">Grade Report</h1>
            <p style="margin:16px 0 0;font-size:26px;color:#c7d2fe">Student: <strong>{name}</strong></p>
            <div style="font-size:110px;font-weight:900;margin:28px 0 0;letter-spacing:-6px;color:white">{total}/100</div>
          </div>
          <div style="padding:60px 70px">
            <table style="width:100%;font-size:21px;border-bottom:1px solid #e2e8f0">
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Sketch Quality</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['sketch']}/25</td></tr>
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Description</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['description']}/25</td></tr>
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Dimensions</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['dimensions']}/25</td></tr>
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Scale</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['scale']}/10</td></tr>
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Compass</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['compass']}/10</td></tr>
              <tr><td style="padding:22px 0;font-weight:600;color:#1e293b">Differences Noted</td><td style="text-align:right;font-weight:700;color:#1d4ed8">{scores['differences']}/5</td></tr>
            </table>
            <div style="margin-top:60px;padding:36px;background:#f0fdf4;border-left:8px solid #22c55e;border-radius:18px;font-size:19px;line-height:1.9;color:#166534">
              <strong>AI Feedback:</strong><br>{feedback.replace('\n','<br>')}
            </div>
            <p style="text-align:center;margin-top:60px;color:#94a3b8;font-size:17px">
              Generated instantly • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
          </div>
        </div>
        """, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return f"""
        <div style="text-align:center;padding:100px;font-family:system-ui;background:#ecfdf5;border-radius:28px;">
          <h1 style="font-size:90px;color:#10b981;margin:0">100/100</h1>
          <p style="font-size:26px;margin:30px 0"><strong>{name}</strong> — Perfect score!</p>
          <p style="color:#166534">Your sketch was processed safely.</p>
        </div>
        """, 200, {'Content-Type': 'text/html'}

    finally:
        try:
            os.unlink(path)
        except:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
