
import os

import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

CONTENT_TYPES = [
    "Short Notes",
    "Detailed Explanation",
    "Important Questions",
    "Quick Revision",
    "Multiple Choice Questions"
]

TONES = [
    "simple English",
    "beginner friendly",
    "exam oriented",
    "professional",
    "easy to remember"
]

# Rough cost estimate
COST_PER_1K_TOKENS = 0.0001


def stream_one(topic, content_type, tone):
    """Generate streamed study material."""

    response = client.chat.stream(
        model="mistral-small-latest",
        temperature=0.8,
        max_tokens=350,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are an expert teacher and study assistant. "
                    f"Generate {content_type.lower()} about the given topic. "
                    f"Use {tone} language. "
                    "Use clear headings, bullet points, and examples where useful. "
                    "Keep the content accurate, educational, and easy to understand."
                ),
            },
            {
                "role": "user",
                "content": f"Study Topic: {topic}",
            },
        ],
    )

    for chunk in response:
        content = chunk.data.choices[0].delta.content

        if content:
            yield content


st.set_page_config(
    page_title="AI Study Notes Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Study Notes Generator")

st.write(
    "Generate easy study notes, explanations, "
    "important questions, and quick revision material."
)

if "history" not in st.session_state:
    st.session_state.history = []

topic = st.text_input(
    "Enter Study Topic",
    placeholder="e.g. Python Exception Handling"
)

content_type = st.selectbox(
    "Select Study Material",
    CONTENT_TYPES
)

tone = st.selectbox(
    "Select Language Style",
    TONES
)

variations = st.checkbox(
    "Generate 3 different versions"
)

generate = st.button("Generate Notes")

regenerate = st.button("Regenerate Notes")


if generate or regenerate:

    if not topic.strip():

        st.warning("Please enter a study topic.")

    else:

        try:

            if variations:

                cols = st.columns(3)

                texts = []

                for index, col in enumerate(cols):

                    with col:

                        st.subheader(f"Version {index + 1}")

                        text = st.write_stream(
                            stream_one(topic, content_type, tone)
                        )

                        texts.append(text or "")

                for index, text in enumerate(texts, start=1):

                    words = len(text.split())

                    tokens = int(words * 1.3)

                    cost = tokens / 1000 * COST_PER_1K_TOKENS

                    st.caption(
                        f"Version {index}: {words} words | "
                        f"~{tokens} tokens | ${cost:.6f}"
                    )

                st.session_state.history.append(
                    {
                        "topic": topic,
                        "type": content_type,
                        "tone": tone,
                        "text": texts[0]
                    }
                )

            else:

                st.subheader("📖 Generated Study Material")

                full_text = st.write_stream(
                    stream_one(topic, content_type, tone)
                )

                full_text = full_text or ""

                words = len(full_text.split())

                tokens = int(words * 1.3)

                cost = tokens / 1000 * COST_PER_1K_TOKENS

                st.metric("Total Words", words)

                st.caption(
                    f"Estimated Tokens: {tokens} | "
                    f"Estimated Cost: ${cost:.6f}"
                )

                st.markdown(full_text)

                st.session_state.history.append(
                    {
                        "topic": topic,
                        "type": content_type,
                        "tone": tone,
                        "text": full_text
                    }
                )

        except Exception as error:

            st.error(f"Something went wrong: {error}")


with st.expander("📚 Study History"):

    if not st.session_state.history:

        st.write("No study material generated yet.")

    else:

        for item in reversed(st.session_state.history):

            st.write(
                f"**{item['type']}** ({item['tone']}) - {item['topic']}"
            )

            st.write(item["text"])

            st.divider()
