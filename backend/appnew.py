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
                #score_items.append((label.replace("_", " ").title(), val))
                score_items.append((label.replace("_", " ").title(), value))
            feedback = data.get("feedback", "Great job!").strip()
        #total = sum(val for _, val in score_items)
        total = sum(int(value.split("/")[0]) for label, value in score_items)
   
        # HTML Output
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>aiGradeMe – Grade Report for {name}</title>
            <style>
                :root {{
                    --gray-50: #f8fafc;
                    --gray-100: #f1f5f9;
                    --gray-300: #cbd5e1;
                    --gray-600: #475569;
                    --gray-800: #1e293b;
                    --gray-900: #0f172a;
                    --purple: #6d28d9;
                    --purple-dark: #5b21b6;
                }}
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background: var(--gray-50);
                    color: var(--gray-800);
                    line-height: 1.6;
                    padding: 2rem 1rem;
                }}
                .card {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 1.5rem;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                    border: 1px solid var(--gray-300);
                }}
                @media (max-width: 640px) {{
                    body {{ padding: 1rem 0.5rem; }}
                    .card {{ border-radius: 1rem; }}
                }}

                .header {{
                    background: white;
                    padding: 2.5rem 2rem;
                    text-align: center;
                    border-bottom: 1px solid var(--gray-300);
                }}
                .header h1 {{
                    font-size: 2.25rem;
                    font-weight: 800;
                    color: var(--gray-900);
                    margin: 0;
                }}
                .header p {{
                    margin: 0.75rem 0 0;
                    color: var(--gray-600);
                    font-size: 1.1rem;
                }}

                .scores {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 2rem 0;
                }}
                .scores td {{
                    padding: 1rem 0;
                    border-bottom: 1px solid var(--gray-300);
                }}
                .label {{ font-weight: 600; color: var(--gray-900); }}
                .value {{ text-align: right; font-weight: 700; color: var(--purple); font-size: 1.25rem; }}

                .total {{
                    text-align: center;
                    padding: 1.5rem;
                    font-size: 1.75rem;
                    font-weight: 800;
                    color: var(--gray-900);
                    background: var(--gray-100);
                }}

                .feedback {{
                    background: var(--gray-100);
                    padding: 2rem;
                    border-radius: 1rem;
                    margin: 2rem 0;
                    border-left: 6px solid var(--gray-600);
                }}
                .feedback h2 {{
                    margin: 0 0 1rem;
                    font-size: 1.5rem;
                    color: var(--gray-900);
                }}
                .feedback p {{
                    margin: 0.75rem 0;
                    color: var(--gray-800);
                }}

                .action {{
                    text-align: center;
                    padding: 2rem;
                }}
                .btn {{
                    display: inline-block;
                    background: var(--purple);
                    color: white;
                    padding: 1rem 2.5rem;
                    border-radius: 1rem;
                    font-size: 1.125rem;
                    font-weight: 700;
                    text-decoration: none;
                    transition: background 0.2s;
                }}
                .btn:hover {{ background: var(--purple-dark); }}
            </style>
        </head>
        <body>
            <div class="card">
                <!-- Header -->
                <header class="header">
                    <h1>{name}'s Grade Report</h1>
                    <p>AI evaluation complete</p>
                </header>

                <!-- Scores -->
                <table class="scores">
                    {"".join(f'<tr><td class="label">{label}</td><td class="value">{value}</td></tr>' for label, value in score_items)}
                </table>

                <!-- Total -->
                <div class="total">Total Score: {total}/100</div>

                <!-- AI Feedback -->
                <section class="feedback">
                    <h2>AI Feedback</h2>
                    <p>{feedback.replace(chr(10), '<br>')}</p>
                </section>

                <!-- Action -->
                <div class="action">
                    <a href="/" class="btn">Grade Another Sketch</a>
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
