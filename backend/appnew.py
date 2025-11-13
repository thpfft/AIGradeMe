# AIGradeMe Backend
# Author: Ron Goodson
# Date: 2025-11-05
# Description:  
# Backend for grading submitted images.

from flask import Flask, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from aichecknew import analyze_image, get_rubric
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
        result = analyze_image(path)
        if "ai_error" in result:
            return f"<p style='text-align:center;color:#dc2626;font-size:18px;margin-top:40px;'>{name} — {result['ai_error']}</p>"
        raw = result["candidates"][0]["content"]["parts"][0]["text"]
        print("RAW API RESPONSE:", raw)
        data = extract_json(raw)
        # === 6 SCORES: AI defines labels & values. No hardcoded names. ===
        if not data or "scores" not in data or not isinstance(data["scores"], dict):
            print("Fallback triggered.")
            score_items = [("Score 1", 0), ("Score 2", 0), ("Score 3", 0), ("Score 4", 0), ("Score 5", 0), ("Score 6", 0)]
            feedback = "AI could not process the image. Please try again."
        else:
            scores_dict = data["scores"]
            # Take first 6 items (in order), convert to int
            items = list(scores_dict.items())[:6]
            if len(items) < 6:
                items += [("Score", 0)] * (6 - len(items))
            score_items = []
            for label, value in items:
                #try:
                #    # val = int(value)
                #    val = int(value.split("/")[0])
                #except:
                #    val = 0
                score_items.append((label.replace("_", " ").title(), val))
            feedback = data.get("feedback", "Great job!").strip()
        total = sum(val for _, val in score_items)
   
        # HTML Output
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
                    <div class="score">{total}</div>
                </div>
                <div class="content">
                    <table>
                        <tr><td class="label">{score_items[0][0]}</td><td class="value">{score_items[0][1]}</td></tr>
                        <tr><td class="label">{score_items[1][0]}</td><td class="value">{score_items[1][1]}</td></tr>
                        <tr><td class="label">{score_items[2][0]}</td><td class="value">{score_items[2][1]}</td></tr>
                        <tr><td class="label">{score_items[3][0]}</td><td class="value">{score_items[3][1]}</td></tr>
                        <tr><td class="label">{score_items[4][0]}</td><td class="value">{score_items[4][1]}</td></tr>
                        <tr><td class="label">{score_items[5][0]}</td><td class="value">{score_items[5][1]}</td></tr>
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
        print(f"CRITICAL ERROR ({type(e).__name__}): {e}")
        return (
            f"<div style='text-align:center;padding:100px;font-family:system-ui;background:#fef2f2'>"
            f"<h1 style='font-size:90px;color:#ef4444;margin:0'>Error</h1>"
            f"<p style='font-size:26px'><strong>{name}</strong> — Something went wrong. Try again.</p>"
            f"</div>",
            500,
            {'Content-Type': 'text/html'}
        )
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
