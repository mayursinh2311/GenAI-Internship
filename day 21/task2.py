import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


# Common function to run all agents
def run_agent(role, content):

    response = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": role
            },
            {
                "role": "user",
                "content": content
            }
        ]
    )

    return response.choices[0].message.content


# Take topic from user
topic = input("Enter a Topic: ")

print("\nMulti Agent System Started...\n")


# Agent 1: Research Agent
print("Agent 1: Research Agent Working...")

research = run_agent(
    "You are a Senior Research Agent. "
    "Analyze the given topic and provide important facts, "
    "The article must be approximately 200 words. "
    "information, key points and examples.",

    f"Research this topic: {topic}"
)

print("Research Completed!\n")


# Agent 2: Writer Agent
print("Agent 2: Writer Agent Working...")

article = run_agent(
    "You are a Professional Article Writer. "
    "Write an engaging and informative article using "
    "The article must be approximately 200 words. "
    "the research provided by the previous agent.",

    f"Topic: {topic}\n\nResearch:\n{research}\n\n"
    "Write a short and meaningful article."
)

print("Article Writing Completed!\n")


# Agent 3: Editor Agent
print("Agent 3: Editor Agent Working...")

edited_article = run_agent(
    "You are a Professional Article Editor. "
    "Correct grammar, spelling, sentence structure "
    "The article must be approximately 200 words. "
    "and improve readability without changing the meaning.",

    f"Edit this article:\n\n{article}"
)

print("Article Editing Completed!\n")


# Agent 4: SEO Agent
print("Agent 4: SEO Agent Working...")

final_article = run_agent(
    "You are an SEO Expert. "
    "Create an attractive SEO-friendly title, "
    "The article must be approximately 200 words. "
    "add relevant keywords and prepare the final article "
    "for publication.",

    f"Prepare the final SEO-friendly article:\n\n{edited_article}"
)

print("\n================================")
print("       FINAL ARTICLE")
print("================================\n")

print(final_article)

print("\nMulti Agent Pipeline Completed!")