# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description:  
# Backend for grading submitted images.

from flask import Flask, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from gemininew import analyze_image, get_rubric
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
        result = gemininew.analyze_image(path)
        try:
            raw = result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            raw = str(result)
        data = extract_json(raw)
        
        # === DEBUG: See what Gemini returns ===
        print("RAW GEMINI RESPONSE:", raw)
        
        if not data or "scores" not in data:
            # === HONEST FALLBACK: No more fake 100% ===
            print("Fallback triggered. Raw length:", len(raw) if raw else 0)
            
            if not raw or len(raw.strip()) < 30:
                scores = {k: 0 for k in ["sketch","description","dimensions","scale","compass","differences"]}
                feedback = "No floor plan detected. Please upload a clear hand-drawn sketch with rooms, labels, dimensions, and scale."

            elif any(word in raw.lower() for word in ["error", "invalid", "unsafe", "cannot", "unable"]):
                scores = {k: 0 for k in ["sketch","description","dimensions","scale","compass","differences"]}
                feedback = "Image rejected: not a valid floor plan. Try a clearer drawing with labels and scale."

            else:
                scores = {k: 0 for k in ["sketch","description","dimensions","scale","compass","differences"]}
                feedback = "AI could not analyze this sketch. Please ensure it's a hand-drawn floor plan with visible details."

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
        # ONLY CHANGE: prettier HTML, same exact return style
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{font-family: -apple-system,system-ui,sans-serif;background:#f9fafb;margin:0;padding:20px}}
                .card {{max-width:820px;margin:40px auto;background:white;border-radius:28px;overflow:hidden;box-shadow:0 25px 70px rgba(0,0,0,0.14)}}
                .header {{background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;padding:70px 50px;text-align:center}}
                .header h1 {{margin:0;font-size:52px;font-weight:900}}
                .header .score {{font-size:110px;font-weight:900;margin:28px 0 0}}
                .content {{padding:60px 70px}}
                table {{width:100%;font-size:21px;border-collapse:collapse}}
                tr {{border-bottom:1px solid #e2e8f0}}
                td {{padding:22px 0}}
                .label {{font-weight:600;color:#1e293b}}
                .value {{text-align:right;font-weight:700;color:#1d4ed8}}
                .feedback {{margin-top:60px;padding:36px;background:#f0fdf4;border-left:8px solid #22c55e;border-radius:18px;font-size:19px;line-height:1.9;color:#166534}}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h1>Grade Report</h1>
                    <p style="margin:16px 0 0;font-size:26px"><strong>{name}</strong></p>
                    <div class="score">{total}/100</div>
                </div>
                <div class="content">
                    <table>
                        <tr><td class="label">Sketch Quality</td><td class="value">{scores['sketch']}/25</td></tr>
                        <tr><td class="label">Description</td><td class="value">{scores['description']}/25</td></tr>
                        <tr><td class="label">Dimensions</td><td class="value">{scores['dimensions']}/25</td></tr>
                        <tr><td class="label">Scale</td><td class="value">{scores['scale']}/10</td></tr>
                        <tr><td class="label">Compass</td><td class="value">{scores['compass']}/10</td></tr>
                        <tr><td class="label">Differences Noted</td><td class="value">{scores['differences']}/5</td></tr>
                    </table>
                    <div class="feedback">
                        <strong>AI Feedback:</strong><br>{feedback.replace('\n','<br>')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        print("CRITICAL ERROR:", str(e))
        return f"<div style='text-align:center;padding:100px;font-family:system-ui;background:#fef2f2'><h1 style='font-size:90px;color:#ef4444;margin:0'>Error</h1><p style='font-size:26px'><strong>{name}</strong> - Something went wrong. Try again.</p></div>", 200, {'Content-Type': 'text/html'}
    finally:
        try:
            os.unlink(path)
        except:
            pass

@app.route("/", methods=["GET"])
def home():
    return "Ready."

@app.route("/rubric", methods=["GET"])
def rubric():
    # Return the student-facing rubric from prompt.txt
    return get_rubric(), 200, {"Content-Type": "text/plain; charset=utf-8"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
