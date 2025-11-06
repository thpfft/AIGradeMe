# utils/grade.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Evaluates submissions against rubric response

def grade_submission(submission):
    """
    submission: {
        "name": str,
        "email": str,
        "analysis": dict  # Gemini JSON response
    }
    """

    gemini_data = submission.get("analysis", {})

    # Default structure in case Gemini fails
    scores = {
        "sketch": None,
        "description": None,
        "dimensions": None,
        "scale": None,
        "compass": None,
        "differences": None,
    }
    feedback = ""

    try:
        feedback = gemini_data.get("feedback", "(No feedback from Gemini.)")
        ai_scores = gemini_data.get("scores", {})
        for key in scores:
            if key in ai_scores:
                scores[key] = ai_scores[key]
    except Exception:
        feedback = "(No feedback from Gemini.)"

    # Compute total only if all scores are numeric
    total = sum(v for v in scores.values() if isinstance(v, (int, float)))

    return {
        "name": submission.get("name", ""),
        "email": submission.get("email", ""),
        "scores": scores,
        "total": total,
        "feedback": feedback,
    }
