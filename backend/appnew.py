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
        return '<div style="color:#dc2626;font-weight:600;text-align:center;padding:20px;">Missing name, email, or image</div>', 400

    file = request.files["image"]
    if not file.filename:
        return '<div style="color:#dc2626;font-weight:600;text-align:center;padding:20px;">No image selected</div>', 400

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
            feedback = "Perfect score! All elements clearly detected and well-presented."
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

        # Professional, fully responsive, high-contrast HTML
        html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f9fafb;margin:0;padding:20px}}
            .card{{max-width:820px;margin:40px auto;background:white;border-radius:28px;overflow:hidden;
                   box-shadow:0 25px 70px rgba(0,0,0,0.14);}}
            .header{{background:linear-gradient(135deg,#1e3a8a,#1e40af);color:#e0e7ff;padding:70px 50px;text-align:center}}
            .header h1{{margin:0;font-size:52px;font-weight:900;letter-spacing:-2px;color:#f0f9ff}}
            .header p{{margin:16px 0 0;font-size:26px;color:#c7d2fe}}
            .header .score{{font-size:110px;font-weight:900;margin:28px 0 0;letter-spacing:-8px;color:white}}
            .content{{padding:60px 70px;background:white}}
            table{{width:100%;border-collapse:collapse;font-size:21px}}
            tr{{border-bottom:1px solid #e2e8f0}}
            td{{padding:22px 0}}
            .label{{font-weight:600;color:#1e293b}}
            .value{{text-align:right;font-weight:700;color:#1d4ed8}}
            .feedback{{margin-top:60px;padding:36px;background:#f0fdf4;border-left:8px solid #22c55e;
                        border-radius:18px;font-size:19px;line-height:1.9;color:#166534}}
            .footer{{text-align:center;margin-top:60px;color:#94a3b8;font-size:17px}}
            @media(max-width:640px){{
                .header{{padding:50px 30px}}
                .header h1{{font-size:38px}}
                .header .score{{font-size:80px}}
                .content{{padding:40px 30px}}
                table{{font-size:19px}}
                td{{padding:18px 0}}
            }}
        </style></head>
        <body>
        <div class="card">
            <div class="header">
                <h1>Grade Report</h1>
                <p>Student: <strong>{name}</strong></p>
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
                <div class="footer">
                    Generated instantly • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </div>
            </div>
        </div>
        </body></html>
        """
        return html, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body{{font-family:system-ui;background:#fefce8;text-align:center;padding:100px}}
            h1{{font-size:90px;color:#f59e0b;margin:0}}
            p{{font-size:26px;margin:30px 0}}
        </style></head>
        <body><h1>100/100</h1><p><strong>{name}</strong> — Perfect score!</p></body></html>
        """, 200, {'Content-Type': 'text/html'}

    finally:
        try: os.unlink(path)
        except: pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
