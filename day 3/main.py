import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

para = input("Enter Your Long Paragraph Here:")

reponse = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.7,
    max_tokens=300,
    messages=[
        {
            "role":"system",
            "content":"You are a smart and reliable AI summarizer. First, accept a long paragraph as input from the user, then automatically analyze and summarize it into a short, simple, and meaningful paragraph. Keep the main ideas, key points, and essential information while removing unnecessary details and repetition. Ensure the summary is accurate, natural, easy to understand, and preserves the original meaning. Once the user submits the paragraph, immediately return the summarized text without asking extra questions or providing additional explanations."
        },
        {
            "role":"user",
            "content":f"Enter Your Long Paragraph Here...{para}, give output on {"summary"}. "
           
        },
    ]
)

print(reponse.choices[0].message.content)