
import os
import json
import streamlit as st
from mistralai.client import Mistral
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Smart Travel Assistant",
    page_icon="🌍",
    layout="centered"
)

st.title("🌍 Smart Travel Assistant Bot")
st.caption("Ask about destinations, travel budgets and travel tips.")

# Travel destinations and estimated prices
destinations = {
    "goa": 8000,
    "manali": 12000,
    "jaipur": 7000,
    "mumbai": 6000,
    "kerala": 15000,
    "kashmir": 18000,
    "udaipur": 9000,
    "shimla": 11000,
    "agra": 5000,
    "rishikesh": 7500
}

# Create tools

def get_destinations():
    result = []
    for place, price in destinations.items():
        result.append(f"{place.title()} - Rs. {price}")
    return json.dumps(result)


def get_budget(place):
    place = place.lower().strip()

    if place in destinations:
        return f"Estimated travel budget for {place.title()} is Rs. {destinations[place]} per person."
    else:
        return "Destination not found in our list."


def web_search(query, tavily_key):
    if not tavily_key:
        return "Tavily API key is missing."

    client = TavilyClient(api_key=tavily_key)

    response = client.search(
        query=query,
        max_results=3
    )

    results = response.get("results", [])

    if not results:
        return "No information found."

    answer = ""

    for result in results:
        answer += result.get("content", "") + "\n"

    return answer


# Tool schema

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_destinations",
            "description": "Get all available travel destinations and budgets",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget",
            "description": "Get estimated travel budget for a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "place": {
                        "type": "string",
                        "description": "Name of travel destination"
                    }
                },
                "required": ["place"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search travel information, tourist places and travel tips",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Travel search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# Tool dispatcher

def tool_call(name, args, tavily_key):

    if name == "get_destinations":
        return get_destinations()

    elif name == "get_budget":
        return get_budget(args["place"])

    elif name == "web_search":
        return web_search(args["query"], tavily_key)

    else:
        return "Tool not found."


# Sidebar API keys

with st.sidebar:
    st.header("🔑 API Keys")

    mistral_key = st.text_input(
        "Mistral API Key",
        value=os.getenv("MISTRAL_API_KEY", ""),
        type="password"
    )

    tavily_key = st.text_input(
        "Tavily API Key",
        value=os.getenv("TAVILY_API_KEY", ""),
        type="password"
    )

    st.caption("API keys can be loaded from .env file.")


# System prompt

system_prompt = (
    "You are a friendly Smart Travel Assistant. "
    "Use get_destinations for destination list questions. "
    "Use get_budget for specific destination budgets. "
    "Use web_search for tourist attractions, travel tips and other travel information. "
    "Keep answers short and simple. "
    "Mention that budgets are estimates, not confirmed prices."
)


# Chat history

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]


# Display chat history

for m in st.session_state.messages:

    role = m["role"] if isinstance(m, dict) else getattr(m, "role", "")

    content = m["content"] if isinstance(m, dict) else getattr(m, "content", "")

    if role in ("user", "assistant") and content:
        st.chat_message(role).write(content)


# User input

prompt = st.chat_input("Ask about your next trip...")

if prompt:

    if not mistral_key:
        st.error("Please add your Mistral API key.")
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    st.chat_message("user").write(prompt)

    client = Mistral(api_key=mistral_key)

    with st.chat_message("assistant"):

        placeholder = st.empty()

        # Tool calling loop

        for _ in range(5):

            msg = client.chat.complete(
                model="mistral-small-latest",
                temperature=0.2,
                messages=st.session_state.messages,
                tools=tools,
                tool_choice="auto"
            )

            response = msg.choices[0].message

            if not response.tool_calls:

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                placeholder.write(response.content)
                break

            st.session_state.messages.append(response)

            for tc in response.tool_calls:

                args = json.loads(tc.function.arguments)

                result = tool_call(
                    tc.function.name,
                    args,
                    tavily_key
                )

                st.session_state.messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc.id
                })

                with st.expander(
                    f"Tool used: {tc.function.name}"
                ):
                    st.write("Arguments:", args)
                    st.write(result)

        else:
            placeholder.warning(
                "Too many tool calls. Please try again."
            )
