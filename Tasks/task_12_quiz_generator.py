import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

topic = input("Enter topic: ")
level = input("Enter difficulty (easy / medium / hard): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.4,
    max_tokens=600,
    messages=[
        {
            "role": "system",
            "content": "You are a teacher. Generate 5 multiple-choice questions with 4 options, correct answer, and 1-line explanation each. Format example - Q: What is 2+2? A) 3 B) 4 C) 5 D) 6 Answer: B Explanation: 2+2 equals 4. First ensure each question is correct, then format. Use only topic details."
        },
        {
            "role": "user",
            "content": f"Topic: {topic} Level: {level} Give 5 quiz questions with options, answers, explanations."
        },
    ]
)

print(response.choices[0].message.content.strip())