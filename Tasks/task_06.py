import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

print("Paste code snippet (press Enter on an empty line to finish):")
lines = []
while True:
    try:
        line = input()
    except EOFError:
        break
    if line.strip() == "":
        break
    lines.append(line)
code = "\n".join(lines).strip()

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.2,
    max_tokens=500,
    messages=[
        {
            "role": "system",
            "content": "You are a senior engineer. Explain the pasted code step by step in plain English, what each part does, then give docstring/comments. Use only code details, no extra assumptions."
        },
        {
            "role": "user",
            "content": f"Code: {code} First explain step by step, then give docstring."
        },
    ]
)

print(response.choices[0].message.content.strip())