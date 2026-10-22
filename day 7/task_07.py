import os
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

text = input("Enter message: ")
target = input("Enter target language: ")
formality = input("Enter formality (formal / casual): ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.3,
    max_tokens=400,
    messages=[
        {
            "role": "system",
            "content": "You are a professional translator. First detect the input language, then translate to the target language in the requested formality. Output only the detection line plus translation, no extra notes."
        },
        {
            "role": "user",
            "content": f"Text: {text} Target: {target} Formality: {formality} First detect input language, then translate."
        },
    ]
)

print(response.choices[0].message.content.strip())