
import streamlit as st
import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

# Initialize Mistral client
api_key = os.getenv("MISTRAL_API_KEY")

st.title("AI STORY GENERATOR")
st.header("Create your own story with AI")

topic = st.text_input("Enter your story topic")
genre = st.selectbox(
    "Choose a story genre",
    ["Adventure", "Horror", "Fantasy", "Romance", "Science Fiction"]
)
length = st.selectbox(
    "Choose story length",
    ["Short", "Medium", "Long"]
)

if st.button("Generate Story"):
    if not api_key:
        st.error("MISTRAL_API_KEY is missing. Please check your .env file.")
    elif not topic.strip():
        st.warning("Please enter a story topic.")
    else:
        try:
            client = Mistral(api_key=api_key)

            with st.spinner("Generating your story..."):
                response = client.chat.stream(
                    model="mistral-small-latest",
                    temperature=0.8,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a creative story writer. "
                                "Write an original, engaging story based "
                                "only on the user's requested topic and "
                                "preferences. Do not use external sources. "
                                "Adjust the story length to the user's choice."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Write a {genre} story about: {topic}. "
                                f"Length: {length}."
                            )
                        }
                    ]
                )

                def token_stream():
                    for chunk in response:
                        content = chunk.data.choices[0].delta.content
                        if content:
                            yield content

                st.subheader("Your Generated Story")
                st.write_stream(token_stream())

        except Exception as e:
            st.error(f"Something went wrong: {e}")
