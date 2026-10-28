
# AI STUDY ASSISTANT

from pypdf import PdfReader
import chromadb
import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

# 1. Read PDF study material

reader = PdfReader("sample.pdf")

text = ""

for page in reader.pages:
    text += page.extract_text() or ""

if not text.strip():
    print("No text found in PDF!")
    exit()

print("Study PDF loaded successfully!")


# 2. Text chunking

def chunks_text(text, chunk_size=500, overlap=100):

    start = 0
    chunks = []

    while start < len(text):

        chunks.append(text[start:start + chunk_size])

        start += chunk_size - overlap

    return chunks


chunks = chunks_text(text)

print("Total chunks:", len(chunks))


# 3. Store text in ChromaDB

client = chromadb.Client()

collection = client.get_or_create_collection(
    name="ai_study_assistant"
)

collection.add(
    documents=chunks,
    ids=[str(i) for i in range(len(chunks))]
)

print("Study material stored successfully!")


# 4. User question

user_input = input("\nAsk your study question: ")


# 5. Find relevant information

relevant = collection.query(
    query_texts=[user_input],
    n_results=4
)

documents = relevant["documents"][0]

context = "\n\n".join(documents)


# 6. Generate AI answer

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    print("MISTRAL_API_KEY is missing in .env file!")
    exit()

client = Mistral(api_key=api_key)

user_prompt = f"""
You are an AI Study Assistant.

Answer the student's question using only
the study material given below.

Explain the answer in simple English.
Use short points and examples when possible.

If the answer is not available in the material,
reply: I don't know.

Study Material:
{context}

Student Question:
{user_input}
"""

response = client.chat.complete(
    model="mistral-small-latest",
    temperature=0.3,
    messages=[
        {
            "role": "user",
            "content": user_prompt
        }
    ]
)


# 7. Display final answer

print("\n========== AI STUDY ASSISTANT ==========")

print(response.choices[0].message.content)

print("========================================")
