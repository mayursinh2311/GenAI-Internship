import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

text = input("Enter user text: ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.1,
    max_tokens=400,
    messages=[
        {
            "role": "system",
            "content": "You are a content moderator. First give reason, then decide Safe / Needs Review / Violates Policy. Examples - Text: 'Great product, loved it!' -> Safe | Text: 'You are stupid, I hate you' -> Violates Policy (harassment) | Text: 'This medicine cures all disease, buy now' -> Needs Review (medical claim). If flagged, give a safe rewritten version. Use only text details."
        },
        {
            "role": "user",
            "content": f"Text: {text} First give reason, then decision, then safe rewrite if flagged."
        },
    ]
)

print(response.choices[0].message.content.strip())