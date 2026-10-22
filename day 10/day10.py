
import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.4,
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": """
            You are an advanced AI-powered product review analyzer.

            Analyze the customer review and return a valid JSON object
            containing exactly these keys:

            1. sentiment:
               "positive", "negative", or "mixed"

            2. rating_score:
               A numeric rating from 1 to 5.
               Use the overall customer experience to determine the rating.

            3. summarize:
               A short summary of the customer's review.

            4. emotions:
               A list of detected emotions, such as happiness,
               satisfaction, frustration, anger, or disappointment.
               Include only emotions supported by the review.

            5. aspects:
               Analyze the following aspects separately:
               - quality
               - delivery
               - price
               - customer_service

               For each aspect, return:
               "positive", "negative", "neutral", or "not_mentioned".

            6. urgency:
               Classify the review as "low", "medium", or "high".
               High urgency means the review indicates a serious issue
               requiring prompt attention, such as a safety concern
               or an urgent unresolved problem.
               Medium means a problem needs attention but is not urgent.
               Low means no significant issue needs immediate attention.

            7. improvement_suggestion:
               Provide a practical suggestion to improve the customer
               experience based on the review.

            8. customer_reply:
               Write a polite, professional, and empathetic response
               to the customer. Address both positive feedback and
               complaints when applicable.

            Important rules:
            - Return valid JSON only.
            - Do not include Markdown or extra text.
            - Use the exact keys specified above.
            - Do not invent details that are absent from the review.
            - Use "not_mentioned" when an aspect is not discussed.
            - Ensure rating_score is a number between 1 and 5.
            """
        },
        {
            "role": "user",
            "content": """
            Analyze this product review:

            "Your product quality is good but delivery is late."

            Return the complete analysis in the required JSON format.
            """
        }
    ]
)

raw = response.choices[0].message.content

print("\n========== RAW AI RESPONSE ==========")
print(raw)

try:
    data = json.loads(raw)

    print("\n========== REVIEW ANALYSIS ==========")

    print("Sentiment:", data["sentiment"])
    print("Rating Score:", data["rating_score"], "/ 5")
    print("Summary:", data["summarize"])

    print("\n--- Emotion Detection ---")
    for emotion in data["emotions"]:
        print("-", emotion)

    print("\n--- Aspect-Based Sentiment ---")
    for aspect, sentiment in data["aspects"].items():
        print(f"{aspect}: {sentiment}")

    print("\nUrgency:", data["urgency"])
    print("Improvement Suggestion:", data["improvement_suggestion"])
    print("Customer Reply:", data["customer_reply"])

except (json.JSONDecodeError, KeyError, TypeError) as e:
    print("Error while parsing or processing JSON:", e)
