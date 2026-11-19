import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def run_agent(role, content):
    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": role,
            },
            {
                "role": "user",
                "content": content
            }
        ]
    )

    return response.choices[0].message.content


topic = input("Enter a Topic: ")

print("Single Agent Starts Working ...")

result = run_agent(
    """You are a Senior Article Researcher, Writer, and Editor.
    Research topics thoroughly, verify facts, and write original,
    engaging, SEO-friendly, high-quality articles.
    Edit and proofread every article for accuracy, grammar,
    clarity, readability, and structure before delivering
    publication-ready content.""",

    f"Write a short article on this topic: {topic}"
)

print("\nGenerated Article:\n")
print(result)