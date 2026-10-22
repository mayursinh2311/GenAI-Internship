import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

reviews = input("Enter reviews separated by | : ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.2,
    max_tokens=500,
    messages=[
        {
            "role": "system",
            "content": "You are a review analyst. Classify each review as Positive / Negative / Neutral, then count totals and give an overall summary of what customers like/dislike. Examples - 'Love the black hoodie, super comfy!' -> Positive | 'Zip broke in 2 days, bad quality' -> Negative | 'Ordered black hoodie, delivered in 3 days' -> Neutral. Use only review details."
        },
        {
            "role": "user",
            "content": f"Reviews: {reviews} Classify each, then counts, then summary."
        },
    ]
)

print(response.choices[0].message.content.strip())