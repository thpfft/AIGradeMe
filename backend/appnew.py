# app.py – Final Production Version (Beautiful HTML + Your Exact Prompt)
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from utils import gemini
import os
import tempfile
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Your exact rubric prompt — locked in and perfect
RUBRIC_PROMPT = """
Evaluate this hand-drawn floor plan sketch according to the rubric:
1. Sketch of a house floor plan, hand drawn, must include labeled rooms (25%).
2. Two sentences describing what the sketch represents (25%).
3. Dimensions of rooms must be present (25%).
4. Scale indicator showing imperial or metric (10%).
5. Compass included (10%).
6. A sentence explaining how this differs from a professional plan (5%).

Please return JSON with the following fields:
{
  "scores": {
    "sketch": int,
    "description": int,
    "dimensions": int,
    "scale": int,
    "compass": int,
    "differences": int
  },
  "feedback": str
}
- Scores should reflect the AI judgment: full points if requirement met, partial if partially met, zero if not included.
- In making the judgement, don't be too strict (be generous, just looking for more serious failures); 100% is very possible
- Provide a short textual explanation in "feedback" (2–4 sentences).
- Output must be valid JSON only, no extra commentary.
"""

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_html(name, scores, feedback, total):
    categories = [
        ("sketch", "Sketch Quality", 25),
        ("description", "Written Description", 25),
        ("dimensions", "Room Dimensions", 25),
        ("scale", "Scale Indicator", 10),
        ("compass", "Compass / North", 10),
        ("differences", "Differences Noted", 5)
    ]

    rows = ""
    for key, label, max_score in categories:
        score = scores.get(key, 0)
        percent = (score / max_score) * 100
        color = "#10b981" if percent >= 80 else "#f59e0b" if percent >= 50 else "#ef4444"
        rows += f"""
        <tr>
            <td class="label">{label}</td>
            <td class="score"><strong>{score}</strong><small>/{max_score}</small></td>
            <td class="progress">
                <div class="bar" style="width: {percent}%; background: {color};"></div>
            </td>
        </tr>"""

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Grade Result – {name}</title>
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; background: #f1f5f9; margin: 0; padding: 1rem; }}
            .card {{ max-width: 680px; margin: 2rem auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; padding: 2.5rem 2rem; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 2.2rem; }}
            .header .name {{ font-size: 1.4rem; opacity: 0.9; margin: 0.5rem 0; }}
            .total {{ font-size: 4rem; font-weight: 900; margin: 0.5rem 0 0; }}
            .content {{ padding: 2rem; }}
            table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
            .label {{ padding: 1rem 0; font-weight: 600; color: #1e293b; }}
            .score {{ text-align: center; font-size: 1.3rem; }}
            .progress {{ height: 28px; background: #e2e8f0; border-radius: 14px; overflow: hidden; }}
            .bar {{ height: 100%; transition: width 1.4s ease; border-radius: 14px; }}
            .feedback {{ background: #f8fafc; padding: 1.8rem; border-radius: 16px; margin-top: 2rem; border-left: 6px solid #3b82f6; font-size: 1.15rem; line-height: 1.7; }}
            .footer {{ text-align: center; margin-top: 2.5rem; color: #64748b; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h1>Grade Result</h1>
                <div class="name">Student: <strong>{name}</strong></div>
                <div class="total">{total}/100</div>
            </div>
            <div class="content">
                <table>{rows}</table>
                <div class="feedback">
                    <strong>AI Feedback:</strong><br>
                    {feedback.replace('\n', '<br>')}
                </div>
                <div class="footer">
                    Instant AI Grading • {__import__('datetime').datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </div>
            </div>
        </div>
    </body>
    </html>
    """.strip()

@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form.get("name", "Student").strip()
        email = request.form.get("email", "").strip()
        if not name or not email:
            return jsonify({"success": False, "error": "Name and email required."}), 400

        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded."}), 400

        file = request.files["image"]
        if not file.filename or not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Please upload a valid image."}), 400

        suffix = os.path.splitext(secure_filename(file.filename))[1] or ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = tmp.name
        tmp.close()
        file.save(temp_path)

        try:
            # Use your exact prompt
            analysis = gemini.analyze_image(temp_path, prompt_override=RUBRIC_PROMPT)

            raw_text = ""
            try:
                raw_text = analysis["candidates"][0]["content"]["parts"][0]["text"]
            except:
                raw_text = str(analysis)

            # Parse JSON safely
            try:
                data = json.loads(raw_text.strip().strip("```json").strip("```"))
                scores = data.get("scores", {})
                feedback = data.get("feedback", "No feedback returned.").strip()
            except:
                scores = {}
                feedback = raw_text.strip() or "Analysis completed."

            # Ensure all keys exist
            default_scores = {"sketch":0,"description":0,"dimensions":0,"scale":0,"compass":0,"differences":0}
            default_scores.update({k: int(v) for k, v in scores.items() if k in default_scores})
            total = sum(default_scores.values())

            html = generate_html(name, default_scores, feedback, total)

            return jsonify({
                "success": True,
                "html": html,
                "total": total,
                "raw_scores": default_scores
            })

        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": "Grading failed. Please try again."}), 500

@app.route("/test", methods=["GET"])
def test():
    test_scores = {"sketch":25,"description":23,"dimensions":25,"scale":10,"compass":10,"differences":5}
    html = generate_html("Test Student", test_scores, "Great job! All elements are clear and complete.", 98)
    return jsonify({"success": True, "html": html})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"AI Grader LIVE on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
