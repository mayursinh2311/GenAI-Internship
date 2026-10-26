
import json
import os

import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Rough cost estimate
COST_PER_1K_TOKENS = 0.0001


def analyze_reviews(reviews, product):
    """Analyze product reviews and return structured results."""

    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.2,
        max_tokens=400,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert product review analyzer. "
                    "Analyze customer reviews about a product. "
                    "Identify customer sentiment, strengths, weaknesses "
                    "and satisfaction level. "
                    "Return ONE JSON object only. "
                    'Keys: "sentiment" (positive, negative, mixed, neutral), '
                    '"satisfaction_score" (integer 0 to 100), '
                    '"positive_points" (list of strings), '
                    '"negative_points" (list of strings), '
                    '"product_quality" (poor, average, good, excellent), '
                    '"recommendation" (buy, consider, avoid). '
                    'Example: Reviews say product is good but expensive -> '
                    '{"sentiment": "mixed", "satisfaction_score": 70, '
                    '"positive_points": ["Good quality"], '
                    '"negative_points": ["High price"], '
                    '"product_quality": "good", "recommendation": "consider"}.'
                ),
            },
            {
                "role": "user",
                "content": f"PRODUCT: {product}\n\nCUSTOMER REVIEWS:\n{reviews}",
            },
        ],
    )

    raw = response.choices[0].message.content

    if raw is None:
        raise ValueError("The model returned no analysis.")

    data = json.loads(raw)

    for key in (
        "sentiment",
        "satisfaction_score",
        "positive_points",
        "negative_points",
        "product_quality",
        "recommendation",
    ):
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    data["satisfaction_score"] = max(
        0, min(100, int(data["satisfaction_score"]))
    )

    tokens = response.usage.total_tokens if response.usage else 0

    return data, tokens


def write_suggestions(reviews, product, result):
    """Generate product improvement suggestions."""

    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.5,
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a product quality consultant. "
                    "Write a short paragraph under 100 words. "
                    "Explain product strengths, customer complaints, "
                    "and suggestions for improvement. "
                    "Use only information from the reviews and analysis."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Product: {product}\n"
                    f"Reviews: {reviews}\n"
                    f"Analysis: {result}"
                ),
            },
        ],
    )

    text = response.choices[0].message.content

    if not text:
        raise ValueError("The model returned no suggestions.")

    tokens = response.usage.total_tokens if response.usage else 0

    return text.strip(), tokens


st.set_page_config(
    page_title="AI Product Review Analyzer",
    page_icon="⭐",
    layout="wide"
)

st.title("⭐ AI Product Review Analyzer")

st.write(
    "Analyze customer reviews and understand product quality, "
    "customer satisfaction, and improvement suggestions."
)

product_text = st.text_input(
    "Product Name",
    placeholder="Example: Samsung Galaxy Smartphone"
)

review_text = st.text_area(
    "Customer Reviews",
    height=250,
    placeholder="Enter customer reviews here..."
)


if st.button("Analyze Reviews"):

    if not product_text.strip():
        st.warning("Please enter a product name.")

    elif not review_text.strip():
        st.warning("Please enter customer reviews.")

    else:
        try:

            with st.spinner("Analyzing customer reviews..."):

                result, analysis_tokens = analyze_reviews(
                    review_text,
                    product_text
                )

            st.subheader("📊 Product Review Analysis")

            st.metric(
                "Customer Satisfaction",
                f"{result['satisfaction_score']}/100"
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Sentiment",
                result["sentiment"].title()
            )

            col2.metric(
                "Product Quality",
                result["product_quality"].title()
            )

            col3.metric(
                "Recommendation",
                result["recommendation"].title()
            )

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("👍 Positive Points")

                for point in result["positive_points"]:
                    st.write(f"✅ {point}")

            with col2:
                st.subheader("👎 Negative Points")

                for point in result["negative_points"]:
                    st.write(f"❌ {point}")

            with st.spinner("Generating improvement suggestions..."):

                suggestions, feedback_tokens = write_suggestions(
                    review_text,
                    product_text,
                    result
                )

            st.subheader("💡 Product Improvement Suggestions")

            edited_suggestions = st.text_area(
                "Edit suggestions",
                value=suggestions,
                height=150
            )

            if st.button("Submit Suggestions"):
                st.success("Suggestions submitted successfully! (Simulated)")
                st.write(edited_suggestions)

            total_tokens = analysis_tokens + feedback_tokens

            cost = total_tokens / 1000 * COST_PER_1K_TOKENS

            st.caption(
                f"Tokens used: {total_tokens} | "
                f"Estimated cost: ${cost:.6f}"
            )

            with st.expander("Raw Analysis JSON"):
                st.json(result)

        except json.JSONDecodeError:
            st.error(
                "The model did not return valid JSON. Please try again."
            )

        except Exception as error:
            st.error(f"Something went wrong: {error}")
