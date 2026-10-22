import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

transcript = input("Paste meeting transcript: ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.2,
    max_tokens=400,
    messages=[
        {
            "role": "system",
            "content": "You are a meeting assistant. Extract action items as Who / What / Deadline, then give a 2-line summary. Use only transcript details. Format examples - Notes: 'Ravi will send report by Friday' -> 1. Who: Ravi | What: Send report | Deadline: Friday | Notes: 'Priya and Amit to fix login bug by Monday, Neha to share designs tomorrow' -> 1. Who: Priya, Amit | What: Fix login bug | Deadline: Monday | 2. Who: Neha | What: Share designs | Deadline: Tomorrow."
        },
        {
            "role": "user",
            "content": f"Transcript: {transcript} First list action items, then 2-line summary."
        },
    ]
)

print(response.choices[0].message.content.strip())