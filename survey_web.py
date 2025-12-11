from flask import render_template, request, Flask
from datetime import datetime
import json
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "<h2>Welcome to the Video Game Survey!</h2><p><a href='/survey'>Start Survey</a></p>"

# --- Competitive questions ---
competitive_questions = [
    {"text": "I feel overwhelmed when playing competitive online games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "Competitive gaming makes me feel nervous or angry.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I experience physical symptoms (e.g., headaches, muscle tension) during competitive matches.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I feel emotionally drained after long competitive gaming sessions.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I worry about my performance or ranking in competitive games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "Toxic interactions (e.g., insults, blame) in competitive games increase my stress levels.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I lose track of time when playing competitive games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I often delay my bedtime due to playing competitive games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}}
]

# --- Singleplayer questions ---
singleplayer_questions = [
    {"text": "I feel relaxed when playing single player games.",
     "options": {"Never": 4, "Rarely": 3, "Sometimes": 2, "Often": 1, "Always": 0}},
    {"text": "Single player games make me feel nervous or angry.",
     "options": {"Never": 4, "Rarely": 3, "Sometimes": 2, "Often": 1, "Always": 0}},
    {"text": "I worry about my performance or ranking in single player games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I feel in control of my emotions when playing single player games.",
     "options": {"Never": 4, "Rarely": 3, "Sometimes": 2, "Often": 1, "Always": 0}},
    {"text": "Playing single player games improves my mood after a difficult day.",
     "options": {"Never": 4, "Rarely": 3, "Sometimes": 2, "Often": 1, "Always": 0}},
    {"text": "I often delay my bedtime due to playing single player games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}},
    {"text": "I worry about my performance or ranking in single player games.",
     "options": {"Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4}}
]

# --- Interpretation helper ---
def interpret(score, thresholds):
    for bound, message in thresholds:
        if score >= bound:
            return message
    return thresholds[-1][1]

# --- Survey route ---
@app.route("/survey", methods=["GET", "POST"])
def run_survey():
    if request.method == "POST":
        name = request.form.get("name")
        student_id = request.form.get("student_id") or "anonymous"
        birth_date_str = request.form.get("birth_date")
        plays_games = request.form.get("plays_games")

        # Parse birth date
        age = None
        birth_date_fmt = birth_date_str
        if birth_date_str and len(birth_date_str) == 8 and birth_date_str.isdigit():
            day = int(birth_date_str[0:2])
            month = int(birth_date_str[2:4])
            year = int(birth_date_str[4:8])
            birth_date_fmt = f"{day:02d}.{month:02d}.{year}"
            birth_date = datetime(year, month, day)
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        if plays_games == "no":
            overall_result = "Survey not conducted (user does not play video games)."
            comp_result = "N/A"
            single_result = "N/A"
        else:
            comp_score = sum(int(request.form.get(f"comp_{i}", 0)) for i in range(len(competitive_questions)))
            single_score = sum(int(request.form.get(f"single_{i}", 0)) for i in range(len(singleplayer_questions)))
            total_score = comp_score + single_score

            overall_result = interpret(total_score, [
                (50, "Severe psychological distress. Professional support may be needed."),
                (38, "High stress levels. You show signs of psychological strain."),
                (26, "Moderate psychological state. Some stress is present but manageable."),
                (14, "Stable psychological state. Occasional stress but generally healthy."),
                (0, "Very healthy psychological state. No significant stress detected.")
            ])
            comp_result = interpret(comp_score, [
                (28, "Severe psychological distress due to competitive online games."),
                (24, "High stress levels due to competitive online games."),
                (15, "Moderate psychological state."),
                (10, "Stable psychological state."),
                (0, "Very healthy psychological state.")
            ])
            single_result = interpret(single_score, [
                (26, "Severe psychological distress due to single player games."),
                (22, "High stress levels due to single player games."),
                (16, "Moderate psychological state."),
                (8, "Stable psychological state."),
                (0, "Very healthy psychological state.")
            ])

        # Build data dictionary
        data = {
            "name": name,
            "student_id": student_id,
            "birth_date": birth_date_fmt,
            "age": age,
            "plays_games": plays_games,
            "overall": overall_result,
            "competitive": comp_result,
            "single_player": single_result
        }

        # Save individual file
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", f"{student_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # Save to master file
        try:
            with open("survey_results.json", "r+", encoding="utf-8") as file:
                all_data = json.load(file)
                all_data.append(data)
                file.seek(0)
                json.dump(all_data, file, indent=4)
        except FileNotFoundError:
            with open("survey_results.json", "w", encoding="utf-8") as file:
                json.dump([data], file, indent=4)

        return render_template("result.html", **data)

    return render_template("survey.html", comp_qs=competitive_questions, single_qs=singleplayer_questions)
@app.route("/results/<student_id>")
def view_results(student_id):
    filepath = os.path.join("results", f"{student_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return render_template("result.html", **data)
    else:
        return f"No results found for student ID {student_id}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

