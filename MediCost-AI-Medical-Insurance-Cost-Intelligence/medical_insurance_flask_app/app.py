"""
Medical Insurance Cost Prediction — Flask Web Application
==========================================================
Updated version:
- ML model prediction
- Gemini AI explanation
- Personalized advice
- 30-day action plan
- Cost-driver visualization data
- Downloadable AI report
- API endpoint
"""

import os
import json
import traceback

import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv

# Gemini safe import
try:
    from google import genai
    GEMINI_IMPORT_ERROR = None
except Exception as e:
    genai = None
    GEMINI_IMPORT_ERROR = str(e)


# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "medical_cost_prediction_model.pkl")

# Load .env from same folder as app.py
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if genai is not None and GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None

print("[INFO] Gemini import working:", genai is not None)
print("[INFO] Gemini API key loaded:", bool(GEMINI_API_KEY))
print("[INFO] Gemini model:", GEMINI_MODEL)

if GEMINI_IMPORT_ERROR:
    print("[WARNING] Gemini import error:", GEMINI_IMPORT_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# Load ML model once
# ─────────────────────────────────────────────────────────────────────────────
MODEL = None
MODEL_ERROR = None

try:
    MODEL = joblib.load(MODEL_PATH)
    print(f"[INFO] Model loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    MODEL_ERROR = (
        f"Model file not found at: {MODEL_PATH}. "
        "Please ensure 'medical_cost_prediction_model.pkl' is in the app directory."
    )
    print(f"[ERROR] {MODEL_ERROR}")
except Exception as e:
    MODEL_ERROR = f"Failed to load model: {str(e)}"
    print(f"[ERROR] {MODEL_ERROR}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature engineering helper
# ─────────────────────────────────────────────────────────────────────────────
def build_features(raw: dict) -> pd.DataFrame:
    age = int(raw["age"])
    gender = raw["gender"]
    bmi = float(raw["bmi"])
    children = int(raw["children"])
    smoker = raw["smoker"]
    region = raw["region"]
    occupation = raw["occupation"]
    annual_income_usd = float(raw["annual_income_usd"])
    exercise_level = raw["exercise_level"]
    chronic_diseases = int(raw["chronic_diseases"])
    doctor_visits_per_year = int(raw["doctor_visits_per_year"])
    hospitalizations_last_year = int(raw["hospitalizations_last_year"])
    alcohol_consumption_per_week = int(raw["alcohol_consumption_per_week"])
    insurance_plan = raw["insurance_plan"]

    if age <= 30:
        age_group = "Young"
    elif age <= 45:
        age_group = "Adult"
    elif age <= 60:
        age_group = "Middle Age"
    else:
        age_group = "Senior"

    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    if annual_income_usd < 40_000:
        income_group = "Low Income"
    elif annual_income_usd < 100_000:
        income_group = "Middle Income"
    else:
        income_group = "High Income"

    smoker_flag = 1 if smoker == "Yes" else 0
    low_ex_flag = 1 if exercise_level == "Low" else 0

    BMI_MAX_REF = 60.0
    ALC_MAX_REF = 30.0
    AGE_MAX_REF = 64.0

    healthcare_utilization_score = doctor_visits_per_year + hospitalizations_last_year * 5

    lifestyle_risk_score = (
        smoker_flag * 3
        + low_ex_flag * 2
        + (alcohol_consumption_per_week / ALC_MAX_REF) * 2
        + (bmi / BMI_MAX_REF) * 1
    )

    health_risk_score = (
        chronic_diseases * 3
        + smoker_flag * 2
        + (bmi / BMI_MAX_REF) * 2
        + (age / AGE_MAX_REF) * 1
    )

    is_high_risk_customer = int(
        smoker == "Yes"
        or chronic_diseases >= 2
        or hospitalizations_last_year >= 2
    )

    score = (
        smoker_flag * 3
        + (2 if chronic_diseases >= 2 else 0)
        + (1 if bmi >= 30 else 0)
        + (2 if hospitalizations_last_year >= 2 else 0)
        + (1 if doctor_visits_per_year >= 8 else 0)
    )

    if score >= 6:
        risk_level = "Very High"
    elif score >= 4:
        risk_level = "High"
    elif score >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    row = {
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "children": children,
        "smoker": smoker,
        "region": region,
        "occupation": occupation,
        "annual_income_usd": annual_income_usd,
        "exercise_level": exercise_level,
        "chronic_diseases": chronic_diseases,
        "doctor_visits_per_year": doctor_visits_per_year,
        "hospitalizations_last_year": hospitalizations_last_year,
        "alcohol_consumption_per_week": alcohol_consumption_per_week,
        "insurance_plan": insurance_plan,

        # Engineered features
        "age_group": age_group,
        "bmi_category": bmi_category,
        "income_group": income_group,
        "healthcare_utilization_score": healthcare_utilization_score,
        "lifestyle_risk_score": lifestyle_risk_score,
        "health_risk_score": health_risk_score,
        "is_high_risk_customer": is_high_risk_customer,
        "risk_level": risk_level,
    }

    return pd.DataFrame([row])


# ─────────────────────────────────────────────────────────────────────────────
# Risk category from predicted cost
# ─────────────────────────────────────────────────────────────────────────────
def cost_risk_category(cost: float) -> dict:
    if cost < 10_000:
        return {"label": "Low Risk", "css_class": "risk-low", "icon": "✅"}
    elif cost <= 25_000:
        return {"label": "Medium Risk", "css_class": "risk-medium", "icon": "⚠️"}
    else:
        return {"label": "High Risk", "css_class": "risk-high", "icon": "🔴"}


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based explanation
# ─────────────────────────────────────────────────────────────────────────────
def generate_explanation(raw: dict, cost: float) -> str:
    reasons = []

    if raw.get("smoker") == "Yes":
        reasons.append("active smoker status")

    bmi = float(raw.get("bmi", 0))
    if bmi >= 30:
        reasons.append(f"obese BMI of {bmi:.1f}")
    elif bmi >= 25:
        reasons.append(f"overweight BMI of {bmi:.1f}")

    cd = int(raw.get("chronic_diseases", 0))
    if cd >= 3:
        reasons.append(f"{cd} chronic diseases")
    elif cd >= 1:
        reasons.append(f"{cd} chronic disease(s)")

    hosp = int(raw.get("hospitalizations_last_year", 0))
    if hosp >= 2:
        reasons.append(f"{hosp} hospitalisations last year")
    elif hosp == 1:
        reasons.append("1 hospitalisation last year")

    visits = int(raw.get("doctor_visits_per_year", 0))
    if visits >= 8:
        reasons.append(f"very high doctor visit frequency: {visits}/year")
    elif visits >= 4:
        reasons.append(f"frequent doctor visits: {visits}/year")

    if raw.get("exercise_level") == "Low":
        reasons.append("low exercise level")

    age = int(raw.get("age", 0))
    if age >= 55:
        reasons.append(f"senior age bracket: {age} years")

    if raw.get("insurance_plan") in ["Premium", "Gold"]:
        reasons.append(f"{raw.get('insurance_plan')} insurance plan")

    alc = int(raw.get("alcohol_consumption_per_week", 0))
    if alc >= 10:
        reasons.append(f"high alcohol consumption: {alc} units/week")

    if not reasons:
        return "This customer shows a generally low-risk profile with no major cost drivers."

    return "Main cost drivers identified: " + "; ".join(reasons) + "."


# ─────────────────────────────────────────────────────────────────────────────
# Fallback chart data
# ─────────────────────────────────────────────────────────────────────────────
def fallback_chart_data(raw: dict) -> list:
    smoker_score = 90 if raw.get("smoker") == "Yes" else 10

    bmi = float(raw.get("bmi", 0))
    if bmi >= 30:
        bmi_score = 80
    elif bmi >= 25:
        bmi_score = 55
    else:
        bmi_score = 25

    chronic = int(raw.get("chronic_diseases", 0))
    chronic_score = min(chronic * 25, 100)

    hospitalizations = int(raw.get("hospitalizations_last_year", 0))
    hospitalization_score = min(hospitalizations * 35, 100)

    visits = int(raw.get("doctor_visits_per_year", 0))
    visits_score = min(visits * 8, 100)

    exercise_score = 75 if raw.get("exercise_level") == "Low" else 35

    alcohol = int(raw.get("alcohol_consumption_per_week", 0))
    alcohol_score = min(alcohol * 6, 100)

    return [
        {"driver": "Smoking", "score": smoker_score},
        {"driver": "BMI", "score": bmi_score},
        {"driver": "Chronic Diseases", "score": chronic_score},
        {"driver": "Hospitalizations", "score": hospitalization_score},
        {"driver": "Doctor Visits", "score": visits_score},
        {"driver": "Exercise", "score": exercise_score},
        {"driver": "Alcohol", "score": alcohol_score},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Fallback advice plan
# ─────────────────────────────────────────────────────────────────────────────
def fallback_ai_plan(raw: dict, cost: float, risk_label: str, rule_explanation: str) -> dict:
    chart_data = fallback_chart_data(raw)

    advice = [
        "Review major cost drivers such as smoking, BMI, chronic conditions, hospital visits, and doctor visit frequency.",
        "Use the prediction as a planning signal to compare insurance coverage, premium, deductible, and expected yearly usage.",
        "Focus on preventive care, regular tracking, and lifestyle consistency to reduce avoidable long-term cost risk."
    ]

    plan = [
        {
            "week": "Week 1",
            "focus": "Profile Review",
            "task": "Review BMI, doctor visits, hospitalisation history, lifestyle habits, and insurance plan coverage."
        },
        {
            "week": "Week 2",
            "focus": "Cost Driver Control",
            "task": "Identify the top 2 risk factors from the chart and create a practical improvement target."
        },
        {
            "week": "Week 3",
            "focus": "Preventive Planning",
            "task": "Plan preventive checkups, track health usage, and document recurring medical expenses."
        },
        {
            "week": "Week 4",
            "focus": "Insurance Optimization",
            "task": "Compare plan type, coverage limits, deductibles, and expected yearly healthcare usage."
        },
    ]

    report = f"""
Medical Insurance AI Report
===========================

Predicted Annual Medical Cost: ${cost:,.2f}
Risk Category: {risk_label}

Cost Explanation:
{rule_explanation}

Personalized Advice:
1. {advice[0]}
2. {advice[1]}
3. {advice[2]}

30-Day Action Plan:
Week 1 - {plan[0]["focus"]}: {plan[0]["task"]}
Week 2 - {plan[1]["focus"]}: {plan[1]["task"]}
Week 3 - {plan[2]["focus"]}: {plan[2]["task"]}
Week 4 - {plan[3]["focus"]}: {plan[3]["task"]}

Disclaimer:
This report is for educational and planning purposes only. It is not medical advice.
"""

    return {
        "advice": advice,
        "plan": plan,
        "chart_data": chart_data,
        "report": report.strip()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Gemini AI explanation
# ─────────────────────────────────────────────────────────────────────────────
def generate_gemini_explanation(raw: dict, cost: float, risk_label: str, rule_explanation: str) -> str:
    print("[INFO] Gemini explanation function called")

    if gemini_client is None:
        print("[WARNING] Gemini client not available. Using rule-based explanation.")
        return rule_explanation

    prompt = f"""
You are an AI explanation assistant for a medical insurance cost prediction dashboard.

Rules:
- Do not give medical diagnosis.
- Do not give medical advice.
- Do not claim certainty.
- Explain in simple business-friendly language.
- Keep it under 180 words.
- Use this exact structure:

Prediction Summary:
Cost Drivers:
Risk Meaning:
Recommendations:

Customer Profile:
Age: {raw.get("age")}
Gender: {raw.get("gender")}
BMI: {raw.get("bmi")}
Children: {raw.get("children")}
Smoker: {raw.get("smoker")}
Region: {raw.get("region")}
Occupation: {raw.get("occupation")}
Annual Income USD: {raw.get("annual_income_usd")}
Exercise Level: {raw.get("exercise_level")}
Chronic Diseases: {raw.get("chronic_diseases")}
Doctor Visits Per Year: {raw.get("doctor_visits_per_year")}
Hospitalizations Last Year: {raw.get("hospitalizations_last_year")}
Alcohol Consumption Per Week: {raw.get("alcohol_consumption_per_week")}
Insurance Plan: {raw.get("insurance_plan")}

Predicted Annual Medical Cost: ${cost:,.2f}
Risk Category: {risk_label}

Rule-based explanation:
{rule_explanation}
"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        print("[INFO] Gemini explanation response received")

        if response and response.text:
            return response.text.strip()

        return rule_explanation

    except Exception as e:
        print(f"[WARNING] Gemini explanation failed: {e}")
        return rule_explanation


# ─────────────────────────────────────────────────────────────────────────────
# Gemini AI advice + plan + chart data + report
# ─────────────────────────────────────────────────────────────────────────────
def generate_gemini_advice_plan(raw: dict, cost: float, risk_label: str, rule_explanation: str) -> dict:
    print("[INFO] Gemini advice/plan function called")

    fallback = fallback_ai_plan(raw, cost, risk_label, rule_explanation)

    if gemini_client is None:
        print("[WARNING] Gemini client not available. Using fallback advice plan.")
        return fallback

    prompt = f"""
You are an AI assistant inside a medical insurance cost prediction dashboard.

Rules:
- Do not give medical diagnosis.
- Do not give medical advice.
- Give lifestyle planning and insurance planning suggestions only.
- Return ONLY valid JSON.
- No markdown.
- No code fences.
- No extra text.

Customer Profile:
Age: {raw.get("age")}
Gender: {raw.get("gender")}
BMI: {raw.get("bmi")}
Children: {raw.get("children")}
Smoker: {raw.get("smoker")}
Region: {raw.get("region")}
Occupation: {raw.get("occupation")}
Annual Income USD: {raw.get("annual_income_usd")}
Exercise Level: {raw.get("exercise_level")}
Chronic Diseases: {raw.get("chronic_diseases")}
Doctor Visits Per Year: {raw.get("doctor_visits_per_year")}
Hospitalizations Last Year: {raw.get("hospitalizations_last_year")}
Alcohol Consumption Per Week: {raw.get("alcohol_consumption_per_week")}
Insurance Plan: {raw.get("insurance_plan")}

Predicted Annual Medical Cost: ${cost:,.2f}
Risk Category: {risk_label}
Rule Explanation: {rule_explanation}

Return JSON exactly like this:

{{
  "advice": [
    "short personalized advice 1",
    "short personalized advice 2",
    "short personalized advice 3"
  ],
  "plan": [
    {{
      "week": "Week 1",
      "focus": "focus title",
      "task": "short task"
    }},
    {{
      "week": "Week 2",
      "focus": "focus title",
      "task": "short task"
    }},
    {{
      "week": "Week 3",
      "focus": "focus title",
      "task": "short task"
    }},
    {{
      "week": "Week 4",
      "focus": "focus title",
      "task": "short task"
    }}
  ],
  "chart_data": [
    {{"driver": "Smoking", "score": 0}},
    {{"driver": "BMI", "score": 0}},
    {{"driver": "Chronic Diseases", "score": 0}},
    {{"driver": "Hospitalizations", "score": 0}},
    {{"driver": "Doctor Visits", "score": 0}},
    {{"driver": "Exercise", "score": 0}},
    {{"driver": "Alcohol", "score": 0}}
  ],
  "report": "downloadable professional report text"
}}

For chart_data score, use 0 to 100 based on estimated contribution strength.
"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        print("[INFO] Gemini advice/plan response received")

        if not response or not response.text:
            return fallback

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)

        return {
            "advice": data.get("advice", fallback["advice"]),
            "plan": data.get("plan", fallback["plan"]),
            "chart_data": data.get("chart_data", fallback["chart_data"]),
            "report": data.get("report", fallback["report"])
        }

    except Exception as e:
        print(f"[WARNING] Gemini advice/plan failed: {e}")
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Form data helper
# ─────────────────────────────────────────────────────────────────────────────
def get_raw_form_data() -> dict:
    return {
        "age": request.form.get("age", "30"),
        "gender": request.form.get("gender", "Male"),
        "bmi": request.form.get("bmi", "25.0"),
        "children": request.form.get("children", "0"),
        "smoker": request.form.get("smoker", "No"),
        "region": request.form.get("region", "Northeast"),
        "occupation": request.form.get("occupation", "Engineer"),
        "annual_income_usd": request.form.get("annual_income_usd", "50000"),
        "exercise_level": request.form.get("exercise_level", "Moderate"),
        "chronic_diseases": request.form.get("chronic_diseases", "0"),
        "doctor_visits_per_year": request.form.get("doctor_visits_per_year", "2"),
        "hospitalizations_last_year": request.form.get("hospitalizations_last_year", "0"),
        "alcohol_consumption_per_week": request.form.get("alcohol_consumption_per_week", "3"),
        "insurance_plan": request.form.get("insurance_plan", "Standard"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Validation helper
# ─────────────────────────────────────────────────────────────────────────────
def validate_inputs(raw: dict) -> list:
    errors = []

    try:
        age = int(raw["age"])
        if not (18 <= age <= 120):
            errors.append("Age must be between 18 and 120.")
    except Exception:
        errors.append("Age must be a valid integer.")

    try:
        bmi = float(raw["bmi"])
        if not (10 <= bmi <= 70):
            errors.append("BMI must be between 10 and 70.")
    except Exception:
        errors.append("BMI must be a valid number.")

    try:
        children = int(raw["children"])
        if not (0 <= children <= 15):
            errors.append("Children must be between 0 and 15.")
    except Exception:
        errors.append("Children must be a valid integer.")

    try:
        income = float(raw["annual_income_usd"])
        if income < 0:
            errors.append("Annual income cannot be negative.")
    except Exception:
        errors.append("Annual income must be a valid number.")

    try:
        chronic = int(raw["chronic_diseases"])
        if not (0 <= chronic <= 10):
            errors.append("Chronic diseases must be between 0 and 10.")
    except Exception:
        errors.append("Chronic diseases must be a valid integer.")

    try:
        visits = int(raw["doctor_visits_per_year"])
        if not (0 <= visits <= 60):
            errors.append("Doctor visits per year must be between 0 and 60.")
    except Exception:
        errors.append("Doctor visits must be a valid integer.")

    try:
        hosp = int(raw["hospitalizations_last_year"])
        if not (0 <= hosp <= 20):
            errors.append("Hospitalisations must be between 0 and 20.")
    except Exception:
        errors.append("Hospitalisations must be a valid integer.")

    try:
        alcohol = int(raw["alcohol_consumption_per_week"])
        if not (0 <= alcohol <= 80):
            errors.append("Alcohol consumption must be between 0 and 80.")
    except Exception:
        errors.append("Alcohol consumption must be a valid integer.")

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Prediction helper
# ─────────────────────────────────────────────────────────────────────────────
def make_prediction(raw: dict) -> dict:
    features_df = build_features(raw)

    predicted_cost = float(MODEL.predict(features_df)[0])
    predicted_cost = max(0.0, round(predicted_cost, 2))

    risk = cost_risk_category(predicted_cost)

    rule_explanation = generate_explanation(raw, predicted_cost)

    ai_explanation = generate_gemini_explanation(
        raw=raw,
        cost=predicted_cost,
        risk_label=risk["label"],
        rule_explanation=rule_explanation
    )

    ai_plan = generate_gemini_advice_plan(
        raw=raw,
        cost=predicted_cost,
        risk_label=risk["label"],
        rule_explanation=rule_explanation
    )

    return {
        "predicted_cost": predicted_cost,
        "risk": risk,
        "rule_explanation": rule_explanation,
        "ai_explanation": ai_explanation,
        "ai_advice": ai_plan["advice"],
        "ai_plan": ai_plan["plan"],
        "chart_data": ai_plan["chart_data"],
        "download_report": ai_plan["report"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", model_error=MODEL_ERROR)


@app.route("/predict", methods=["POST"])
def predict():
    if MODEL is None:
        return render_template(
            "index.html",
            model_error=MODEL_ERROR or "Model is not available."
        )

    try:
        raw = get_raw_form_data()

        errors = validate_inputs(raw)
        if errors:
            return render_template(
                "index.html",
                model_error=None,
                form_errors=errors,
                form_data=raw
            )

        prediction_result = make_prediction(raw)

        predicted_cost = prediction_result["predicted_cost"]
        risk = prediction_result["risk"]

        input_summary = [
            ("Age", f"{raw['age']} years"),
            ("Gender", raw["gender"]),
            ("BMI", f"{float(raw['bmi']):.1f}"),
            ("Children", raw["children"]),
            ("Smoker", raw["smoker"]),
            ("Region", raw["region"]),
            ("Occupation", raw["occupation"]),
            ("Annual Income", f"${float(raw['annual_income_usd']):,.0f}"),
            ("Exercise Level", raw["exercise_level"]),
            ("Chronic Diseases", raw["chronic_diseases"]),
            ("Doctor Visits / Year", raw["doctor_visits_per_year"]),
            ("Hospitalisations Last Year", raw["hospitalizations_last_year"]),
            ("Alcohol Units / Week", raw["alcohol_consumption_per_week"]),
            ("Insurance Plan", raw["insurance_plan"]),
        ]

        return render_template(
            "result.html",
            predicted_cost=f"{predicted_cost:,.2f}",
            risk_label=risk["label"],
            risk_class=risk["css_class"],
            risk_icon=risk["icon"],

            explanation=prediction_result["ai_explanation"],
            rule_explanation=prediction_result["rule_explanation"],
            input_summary=input_summary,

            gemini_enabled=gemini_client is not None,
            ai_advice=prediction_result["ai_advice"],
            ai_plan=prediction_result["ai_plan"],
            chart_data=json.dumps(prediction_result["chart_data"]),
            download_report=prediction_result["download_report"],
        )

    except Exception:
        tb = traceback.format_exc()
        print(f"[ERROR] Prediction failed:\n{tb}")

        return render_template(
            "index.html",
            model_error=(
                "An unexpected error occurred during prediction. "
                "Please check your inputs and try again."
            )
        )


@app.route("/download-report", methods=["POST"])
def download_report():
    report_text = request.form.get("report_text", "No report available.")

    return Response(
        report_text,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=medical_insurance_ai_report.txt"
        }
    )


@app.route("/api/predict", methods=["POST"])
def api_predict():
    if MODEL is None:
        return jsonify({
            "success": False,
            "error": MODEL_ERROR or "Model is not available."
        }), 500

    try:
        raw = request.get_json()

        if raw is None:
            return jsonify({
                "success": False,
                "error": "Invalid JSON input."
            }), 400

        errors = validate_inputs(raw)
        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        prediction_result = make_prediction(raw)
        predicted_cost = prediction_result["predicted_cost"]
        risk = prediction_result["risk"]

        return jsonify({
            "success": True,
            "predicted_cost": predicted_cost,
            "risk_label": risk["label"],
            "risk_class": risk["css_class"],
            "risk_icon": risk["icon"],
            "gemini_enabled": gemini_client is not None,
            "explanation": prediction_result["ai_explanation"],
            "rule_based_explanation": prediction_result["rule_explanation"],
            "ai_advice": prediction_result["ai_advice"],
            "ai_plan": prediction_result["ai_plan"],
            "chart_data": prediction_result["chart_data"],
            "download_report": prediction_result["download_report"],
        })

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] API prediction failed:\n{tb}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ─────────────────────────────────────────────────────────────────────────────
# Run app
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)