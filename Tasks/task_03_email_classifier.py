import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

email = input("Enter incoming email: ")

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.2,
    max_tokens=400,
    messages=[
        {
            "role": "system",
            "content": "You are a support inbox sorter. First classify the email as Urgent / Billing / General / Spam, then write an appropriate reply using only email details. Examples - Email: 'Server down, all orders failing!' -> Category: Urgent | Email: 'Charged twice for order 123' -> Category: Billing | Email: 'Do you ship to Pune?' -> Category: General | Email: 'Win free crypto now!!!' -> Category: Spam."
        },
        {
            "role": "user",
            "content": f"Email: {email} First output Category, then write reply."
        },
    ]
)

print(response.choices[0].message.content.strip())