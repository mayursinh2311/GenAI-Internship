import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

role = input("Enter job role: ")
level = input("Enter difficulty (easy / medium / hard): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.5,
    max_tokens=500,
    messages=[
        {
            "role": "system",
            "content": "You are a technical interviewer. Generate 5 interview questions for the role and level, split into Technical and Behavioral, each with ideal answer points. Use only role and level details."
        },
        {
            "role": "user",
            "content": f"Role: {role} Level: {level} First plan coverage, then give questions with answer points."
        },
    ]
)

print(response.choices[0].message.content.strip())