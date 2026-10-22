import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

product = input("Enter product name: ")
features = input("Enter 3-4 features (comma separated): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.9,
    max_tokens=500,
    messages=[
        {
            "role": "system",
            "content": "You are a persuasive marketing copywriter. Write 3 description variations for A/B testing, each with a short tagline, using only the given product and features. Keep each description 40-60 words."
        },
        {
            "role": "user",
            "content": f"Product: {product} Features: {features} Give 3 variations, each with Description + Tagline."
        },
    ]
)

print(response.choices[0].message.content.strip())