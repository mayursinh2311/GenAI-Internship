import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

topic = input("Enter topic: ")
platform = input("Enter platform (Twitter / LinkedIn / Instagram / all): ")
tone = input("Enter tone: ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.8,
    max_tokens=450,
    messages=[
        {
            "role": "system",
            "content": "You are a social media manager. Size the post to the platform. Examples - Twitter: short under 280 chars + 2 hashtags | LinkedIn: professional 80-100 words + 3 hashtags | Instagram: casual with emojis + 5 hashtags. If platform is all, give all 3 posts. Use only topic details."
        },
        {
            "role": "user",
            "content": f"Topic: {topic} Platform: {platform} Tone: {tone} Write post with hashtags."
        },
    ]
)

print(response.choices[0].message.content.strip())