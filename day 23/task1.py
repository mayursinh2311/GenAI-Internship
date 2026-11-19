
import json
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from mistralai.client import Mistral

load_dotenv()

# Load API Keys
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

mistral_client = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MISTRAL_MODEL = "mistral-small-latest"
JUDGE_MODEL = "openai/gpt-oss-20b"


# Evaluation Prompt
JUDGE_PROMPT = """
You are a professional AI Answer Evaluator.

Your task is to evaluate answers on ANY topic.

Check the following:
1. Factual correctness.
2. Completeness of the answer.
3. Relevance to the question.
4. Clarity and readability.
5. Quality of information.

Give an honest score from 0 to 10.

Reply with ONE JSON object only.

Keys:
"score": integer from 0 to 10,
"verdict": one of "poor", "fair", "good", "excellent",
"strengths": list of short strings,
"weaknesses": list of short strings,
"summary": one or two sentences.
"""


# Mistral AI - Generate Answer
def ask_mistral(question):

    response = mistral_client.chat.complete(
        model=MISTRAL_MODEL,
        temperature=0.6,
        messages=[
            {
                "role": "system",
                "content": "You are a professional AI assistant. Answer questions about any topic using clear, simple, accurate and informative language."
            },
            {
                "role": "user",
                "content": question
            }
        ],
    )

    answer = response.choices[0].message.content

    if not answer:
        raise ValueError("Mistral returned an empty answer.")

    return answer.strip()


# Groq AI - Evaluate Answer
def evaluate_answer(question, answer):

    response = groq_client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": JUDGE_PROMPT
            },
            {
                "role": "user",
                "content": f"""
                Topic / Question: {question}

                Answer to evaluate:
                {answer}
                """
            }
        ],
    )

    raw = response.choices[0].message.content

    if not raw:
        raise ValueError("Groq returned an empty evaluation.")

    return raw.strip()


# Parse JSON Evaluation
def parse_evaluation(raw):

    text = raw.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Invalid JSON response.")

    data = json.loads(text[start:end + 1])

    for key in ("score", "verdict", "strengths", "weaknesses", "summary"):
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    data["score"] = max(0, min(10, int(data["score"])))
    data["verdict"] = str(data["verdict"]).lower()
    data["strengths"] = [str(x) for x in data["strengths"]]
    data["weaknesses"] = [str(x) for x in data["weaknesses"]]
    data["summary"] = str(data["summary"])

    return data


# Streamlit UI
st.set_page_config(
    page_title="Any Topic AI Evaluator",
    page_icon="🤖",
    layout="centered"
)

st.title("Any Topic AI Answer Evaluator")

st.caption(
    "Mistral generates answers and Groq evaluates their quality."
)

# User Input
question = st.text_area(
    "Enter Any Topic or Question",
    height=120,
    placeholder="Example: Explain Artificial Intelligence..."
)


# Generate and Evaluate Button
if st.button("Generate & Evaluate"):

    if not question.strip():

        st.warning("Please enter a topic or question.")

    elif mistral_client is None or groq_client is None:

        st.error("Please add MISTRAL_API_KEY and GROQ_API_KEY to your .env file.")

    else:

        try:

            # Step 1 - Generate Answer
            with st.spinner("Mistral AI is generating an answer..."):

                answer = ask_mistral(question.strip())

            st.subheader("Mistral AI Answer")
            st.write(answer)


            # Step 2 - Evaluate Answer
            with st.spinner("Groq AI is evaluating the answer..."):

                raw = evaluate_answer(question.strip(), answer)


            # Step 3 - Display Evaluation
            st.subheader("Groq AI Evaluation")

            try:

                evaluation = parse_evaluation(raw)

                st.metric(
                    "Answer Score",
                    f"{evaluation['score']} / 10"
                )

                st.write(
                    f"**Verdict:** {evaluation['verdict'].title()}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write("### Strengths")

                    for item in evaluation["strengths"]:
                        st.write(f"- {item}")

                with col2:

                    st.write("### Weaknesses")

                    for item in evaluation["weaknesses"]:
                        st.write(f"- {item}")

                st.write("### Summary")
                st.write(evaluation["summary"])

                with st.expander("View Evaluation Details"):
                    st.json(evaluation)

            except (ValueError, json.JSONDecodeError):

                st.warning("Unable to parse evaluation JSON.")
                st.write(raw)

        except Exception as error:

            st.error(f"Something went wrong: {error}")
