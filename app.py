import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

app = Flask(__name__)
CORS(app)

MODEL = "gemini-2.5-flash"


class Exercise(BaseModel):
    name: str = Field(description="Name of the exercise")
    sets: int = Field(description="Number of sets")
    reps: str = Field(description="Number of reps or duration")
    instructions: str = Field(description="Brief execution tip")


class WorkoutDay(BaseModel):
    day_name: str = Field(description="e.g., Day 1 - Push")
    focus: str = Field(description="Muscle group or workout focus")
    exercises: list[Exercise]


class Meal(BaseModel):
    meal_type: str = Field(description="Breakfast, Lunch, Dinner, or Snack")
    description: str = Field(description="Dish using local style and preferences")


class FitBuddyCompletePlan(BaseModel):
    user_summary: str = Field(description="Summary of user metrics, goals, targets")
    workout_schedule: list[WorkoutDay]
    nutrition_plan: list[Meal]


def _int(value, default, lo, hi):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def _float(value, default, lo, hi):
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def _get_client():
    """Create a Gemini client from the request header or environment."""
    api_key = (request.headers.get("X-Gemini-API-Key") or os.getenv("GEMINI_API_KEY")
               or os.getenv("GOOGLE_API_KEY"))
    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. Enter your key in the FitBuddy sidebar "
            "or set GEMINI_API_KEY in the environment."
        )
    return genai.Client(api_key=api_key)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/generate-comprehensive-plan")
def generate_comprehensive_plan():
    data = request.get_json(silent=True) or {}

    age = _int(data.get("age"), 19, 10, 100)
    gender = str(data.get("gender", "Male"))[:30]
    environment = str(data.get("environment", "gym"))[:30]
    days = _int(data.get("workout_days_per_week"), 5, 1, 7)
    duration = _int(data.get("workout_duration_minutes"), 45, 15, 120)
    goal = str(data.get("main_goal", "weight_loss")).replace("_", " ")
    target_kg = _float(data.get("target_kg"), 5, 0.5, 50)
    want_abs = bool(data.get("want_abs", True))
    state = str(data.get("state_location", "Tamil Nadu"))[:60]
    veg_status = str(data.get("vegetarian_status", "Vegetarian"))[:30]
    food_style = str(data.get("food_style", "Home food"))[:30]
    height_cm = _float(data.get("height_cm"), 165, 100, 230)
    weight_kg = _float(data.get("weight_kg"), 60, 25, 250)

    prompt = f"""
You are FitBuddy, an expert AI fitness coach. Craft a customized routine.
- Age/Gender: {age} yrs, {gender}
- Height/Weight: {height_cm} cm, {weight_kg} kg
- Workout Environment: {environment}
- Schedule: {days} workout days per week, with remaining days as rest/recovery
- Session duration: {duration} minutes
- Primary Goal: {goal} (target change: {target_kg} kg)
- Abs focus: {'Yes, include core/abs work' if want_abs else 'No, standard routine'}
- Location: {state}, India
- Dietary Type: {veg_status}
- Food Style: {food_style}

Provide:
1. A short summary acknowledging the goals and a safe, realistic pace. Do not prescribe extreme dieting.
2. EXACTLY {days} workout days, each fitting about {duration} minutes and using only {environment} equipment.
3. A full day of meals (Breakfast, Lunch, Snack, Dinner) using local {state} ingredients that respect the {veg_status} preference and {food_style} style.
"""
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FitBuddyCompletePlan,
                temperature=0.7,
            ),
        )
        if response.parsed is not None:
            return jsonify(response.parsed.model_dump())
        plan = FitBuddyCompletePlan.model_validate(json.loads(response.text))
        return jsonify(plan.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/chat")
def fitness_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])
    plan_summary = str(data.get("plan_summary", ""))[:1500]

    if not message:
        return jsonify({"error": "Message is required"}), 400

    system_instruction = (
        "You are FitBuddy's AI fitness chatbot. Help users step-by-step with "
        "gym/home workouts, exercise form, motivation, and local healthy food "
        "options. Be concise, encouraging, and clear. Do not encourage extreme "
        "dieting or unsafe exercise. For injuries or medical conditions, suggest "
        "talking to a qualified healthcare professional."
    )
    if plan_summary:
        system_instruction += f"\nUser's current plan summary: {plan_summary}"

    contents = []
    for turn in history[-20:]:
        role = "model" if turn.get("role") == "assistant" else "user"
        text = str(turn.get("content", ""))
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction, temperature=0.7
            ),
        )
        return jsonify({"response": response.text or "I couldn't generate a reply."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=5000)
