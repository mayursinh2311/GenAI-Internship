import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

complaint = input("Enter customer complaint: ")
tone = input("Enter tone (polite / formal / friendly / auto): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.3,
    max_tokens=350,
    messages=[
        {
            "role": "system",
            "content": "You are a professional e-commerce support agent. First output Severity: Low / Medium / High based on the complaint. Then write a reply in the requested tone, using only complaint details. If tone is auto, detect angry or neutral from the complaint and pick the tone yourself."
        },
        {
            "role": "user",
            "content": f"Complaint: {complaint} Tone: {tone} First classify severity, then write reply."
        },
    ]
)

print(response.choices[0].message.content.strip())