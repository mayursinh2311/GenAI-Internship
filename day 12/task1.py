
import json
import os

import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

TONES = ["motivational", "professional", "friendly"]

# Rough cost estimate
COST_PER_1K_TOKENS = 0.0001


def analyze(message):
    """Analyze student performance and return structured data."""

    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.2,
        max_tokens=200,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI student performance analyzer. "
                    "Analyze the student's marks, academic performance, "
                    "strengths, and weaknesses. "
                    "Use only the information provided by the student. "
                    "Do not invent marks or percentages. "
                    "Return ONE JSON object only. "
                    'Keys: "performance" (excellent, good, average, needs improvement), '
                    '"category" (academic, attendance, assignment, exam, general), '
                    '"study_priority" (integer 1 to 5), '
                    '"strength" (short phrase, max 8 words), '
                    '"improvement_area" (short phrase, max 8 words). '
                    'Example: "I scored 85 in mathematics" -> '
                    '{"performance": "excellent", "category": "academic", '
                    '"study_priority": 2, "strength": "good mathematics performance", '
                    '"improvement_area": "continue regular practice"}.'
                ),
            },
            {"role": "user", "content": message},
        ],
    )

    raw = response.choices[0].message.content

    if raw is None:
        raise ValueError("The model returned no analysis.")

    data = json.loads(raw)

    for key in (
        "performance",
        "category",
        "study_priority",
        "strength",
        "improvement_area",
    ):
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    data["study_priority"] = max(
        1, min(5, int(data["study_priority"]))
    )

    tokens = response.usage.total_tokens if response.usage else 0

    return data, tokens


def draft_feedback(message, analysis, tone):
    """Generate student feedback."""

    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.7,
        max_tokens=250,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a student academic mentor. "
                    f"Write feedback in a {tone} tone. "
                    "Use only details from the student's message "
                    "and the analysis. "
                    "Keep it under 120 words. "
                    "Give useful study suggestions. "
                    "Do not invent marks or achievements. "
                    "End with a clear next step."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Student details: {message}\n"
                    f"Analysis: performance={analysis['performance']}, "
                    f"category={analysis['category']}, "
                    f"study priority={analysis['study_priority']}, "
                    f"strength={analysis['strength']}, "
                    f"improvement area={analysis['improvement_area']}"
                ),
            },
        ],
    )

    feedback = response.choices[0].message.content

    if not feedback:
        raise ValueError("The model returned no feedback.")

    tokens = response.usage.total_tokens if response.usage else 0

    return feedback.strip(), tokens


st.set_page_config(
    page_title="AI Student Performance Analyzer",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Student Performance Analyzer")

st.write(
    "Analyze student performance and generate "
    "personalized academic feedback."
)

message = st.text_area(
    "Student Details and Marks",
    height=150,
    placeholder=(
        "Example: My name is Rahul. "
        "I scored 85 in English, 75 in Maths, "
        "and 60 in Science. I need help improving Science."
    ),
)

auto_tone = st.checkbox(
    "Auto-pick feedback tone",
    value=True
)

tone = st.selectbox(
    "Feedback Tone",
    TONES,
    disabled=auto_tone
)


if st.button("Analyze Performance"):

    if not message.strip():
        st.warning("Please enter student details.")

    else:
        try:
            with st.spinner("Analyzing student performance..."):

                analysis, analysis_tokens = analyze(message)

            if auto_tone:
                tone_used = {
                    "excellent": "friendly",
                    "good": "motivational",
                    "average": "professional",
                    "needs improvement": "motivational",
                }.get(
                    analysis["performance"],
                    "professional"
                )
            else:
                tone_used = tone

            with st.spinner("Generating academic feedback..."):

                feedback, feedback_tokens = draft_feedback(
                    message,
                    analysis,
                    tone_used
                )

            st.session_state.result = {
                "analysis": analysis,
                "feedback": feedback,
                "tone_used": tone_used,
                "tokens": analysis_tokens + feedback_tokens,
            }

        except json.JSONDecodeError:
            st.error("Invalid JSON response. Please try again.")

        except Exception as error:
            st.error(f"Something went wrong: {error}")


if "result" in st.session_state:

    result = st.session_state.result
    analysis = result["analysis"]

    st.subheader("📊 Student Performance Analysis")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Performance",
        analysis["performance"].title()
    )

    col2.metric(
        "Study Priority",
        f"{analysis['study_priority']}/5"
    )

    col3.metric(
        "Category",
        analysis["category"].title()
    )

    st.write("**💪 Student Strength:**", analysis["strength"])

    st.write(
        "**📚 Improvement Area:**",
        analysis["improvement_area"]
    )

    st.write(
        "**Feedback Tone:**",
        result["tone_used"].title()
    )

    st.subheader("📝 Personalized Academic Feedback")

    edited_feedback = st.text_area(
        "Edit feedback",
        value=result["feedback"],
        height=180
    )

    if st.button("Submit Feedback"):
        st.success("Feedback submitted successfully! (Simulated)")
        st.write(edited_feedback)

    tokens = result["tokens"]

    cost = tokens / 1000 * COST_PER_1K_TOKENS

    st.caption(
        f"Tokens Used: {tokens} | "
        f"Estimated Cost: ${cost:.6f}"
    )

    with st.expander("View Raw Analysis JSON"):
        st.json(analysis)
