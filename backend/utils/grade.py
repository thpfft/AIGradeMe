# utils/grade.py
# Author: Ron Goodson
# Date: 2025-11-05
# Description: Evaluates submissions against rubric.

def grade_submission(submission_data):
    """
    Placeholder function to grade a submission.
    Returns dummy scores for now.
    """
    return {
        "name": submission_data.get("name", ""),
        "email": submission_data.get("email", ""),
        "scores": {
            "sketch": 25,
            "description": 25,
            "dimensions": 25,
            "scale": 10,
            "compass": 10,
            "differences": 5
        },
        "total": 100,
        "feedback": "All criteria met (dummy data)."
    }
