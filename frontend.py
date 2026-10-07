import requests
import streamlit as st

st.set_page_config(page_title="FitBuddy", page_icon="💪", layout="wide")

BACKEND_URL = "http://127.0.0.1:5000/api"

# --- Session state ---
st.session_state.setdefault("plan_data", None)
st.session_state.setdefault("plan_meta", {})
st.session_state.setdefault("chat_history", [])

st.title("💪 FitBuddy – AI Fitness Plan & Nutrition Generator")
st.markdown("Personalized gym/home workouts, progress tracking, and regional nutrition.")

# --- Sidebar form ---
st.sidebar.header("🔑 Gemini API")
gemini_api_key = st.sidebar.text_input(
    "Gemini API key", type="password", help="Your key is sent only to your local Flask backend."
)

st.sidebar.header("👤 Tell Us About Yourself")
with st.sidebar.form("onboarding_form"):
    age = st.number_input("Age", min_value=10, max_value=100, value=19)
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=230, value=165)
    weight_kg = st.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=60.0)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    st.subheader("Workout Preferences")
    environment = st.selectbox("Environment", ["gym", "home"], format_func=str.title)
    workout_days = st.slider("Workout days per week", 1, 7, 5)
    workout_duration = st.slider("Session duration (min)", 15, 120, 45, step=15)

    st.subheader("Goals")
    main_goal = st.selectbox(
        "Primary goal",
        ["weight_loss", "weight_gain", "muscle_building"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    target_kg = st.number_input("Kg to lose or gain", min_value=1.0, max_value=30.0, value=5.0)
    want_abs = st.checkbox("Include Abs/Core training", value=True)

    st.subheader("Diet")
    state_location = st.text_input("State / Region", "Tamil Nadu")
    veg_status = st.selectbox("Dietary type", ["Vegetarian", "Non-vegetarian", "Mixed"])
    food_style = st.selectbox("Food style", ["Home food", "Diet food"])

    submitted = st.form_submit_button("🚀 Generate My Plan")

if submitted:
    payload = {
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "gender": gender,
        "environment": environment,
        "workout_days_per_week": workout_days,
        "workout_duration_minutes": workout_duration,
        "main_goal": main_goal,
        "target_kg": target_kg,
        "want_abs": want_abs,
        "state_location": state_location,
        "vegetarian_status": veg_status,
        "food_style": food_style,
    }
    with st.spinner("🤖 Designing your plan..."):
        try:
            res = requests.post(
                f"{BACKEND_URL}/generate-comprehensive-plan",
                json=payload,
                headers={"X-Gemini-API-Key": gemini_api_key} if gemini_api_key else {},
                timeout=120,
            )
            if res.status_code == 200:
                # Reset old progress/checkboxes/chat for the new plan
                for k in [k for k in st.session_state if str(k).startswith("day_")]:
                    del st.session_state[k]
                st.session_state.chat_history = []
                st.session_state.plan_data = res.json()
                st.session_state.plan_meta = {
                    "state": state_location,
                    "veg": veg_status,
                    "style": food_style,
                }
                st.success("Plan generated!")
            else:
                st.error(f"Server error: {res.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the Flask backend. Is app.py running? ({e})")

# --- Dashboard ---
if st.session_state.plan_data:
    plan = st.session_state.plan_data
    meta = st.session_state.plan_meta
    st.info(f"📋 **Plan Summary:** {plan.get('user_summary', '')}")

    tab1, tab2, tab3 = st.tabs(["🏋 Workouts", "🍎 Nutrition", "💬 Coach Chat"])

    with tab1:
        st.subheader("Your Workout Routine")
        total = done = 0
        for d_idx, day in enumerate(plan.get("workout_schedule", [])):
            with st.expander(f"📅 {day['day_name']} — {day['focus']}"):
                for e_idx, ex in enumerate(day.get("exercises", [])):
                    total += 1
                    checked = st.checkbox(
                        f"**{ex['name']}** | {ex['sets']} × {ex['reps']} (Tip: {ex['instructions']})",
                        key=f"day_{d_idx}_ex_{e_idx}",
                    )
                    done += int(checked)
        if total:
            pct = int(done / total * 100)
            st.metric("📊 Progress", f"{pct}%", f"{done}/{total} completed")
            st.progress(pct / 100)

    with tab2:
        st.subheader(f"🍎 Nutrition Plan ({meta.get('state', '')} Style)")
        st.markdown(
            f"Tailored for **{meta.get('veg', '')}** using **{meta.get('style', '')}** options."
        )
        for meal in plan.get("nutrition_plan", []):
            st.markdown(f"* **{meal['meal_type']}:** {meal['description']}")

    with tab3:
        st.subheader("💬 FitBuddy Chatbot")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        query = st.chat_input("Ask about form, alternatives, motivation, or diet...")
        if query:
            with st.chat_message("user"):
                st.markdown(query)
            with st.spinner("FitBuddy is typing..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/chat",
                        headers={"X-Gemini-API-Key": gemini_api_key} if gemini_api_key else {},
                        json={
                            "message": query,
                            "history": st.session_state.chat_history,
                            "plan_summary": plan.get("user_summary", ""),
                        },
                        timeout=60,
                    )
                    reply = (
                        res.json().get("response", "No response.")
                        if res.status_code == 200
                        else "Sorry, the server returned an error."
                    )
                except requests.exceptions.RequestException as e:
                    reply = f"Error connecting to backend: {e}"
            st.session_state.chat_history.append({"role": "user", "content": query})
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
else:
    st.warning("👈 Fill in your profile in the sidebar and click **Generate My Plan**.")
