import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

points = input("Enter your key points: ")
job = input("Enter job description: ")
tone = input("Enter tone (confident / humble / enthusiastic): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.6,
    max_tokens=500,
    messages=[
        {
            "role": "system",
            "content": "You are a career coach. First match candidate skills to job requirements, then write a tailored professional cover letter in the requested tone. Use only given details."
        },
        {
            "role": "user",
            "content": f"My points: {points} Job: {job} Tone: {tone} First match skills, then write letter."
        },
    ]
)

print(response.choices[0].message.content.strip())