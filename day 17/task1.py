
import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# bus information: route -> list of (time, destination, price, bus)
buses = {
    "ahmedabad": [
        ("8:00 AM", "Vadodara", 150, "Express Bus"),
        ("10:00 AM", "Surat", 250, "AC Bus"),
        ("12:00 PM", "Rajkot", 300, "Express Bus"),
    ],
    "vadodara": [
        ("9:00 AM", "Ahmedabad", 150, "Express Bus"),
        ("11:00 AM", "Surat", 180, "AC Bus"),
        ("2:00 PM", "Mumbai", 500, "Sleeper Bus"),
    ],
    "surat": [
        ("7:00 AM", "Ahmedabad", 250, "AC Bus"),
        ("10:00 AM", "Vadodara", 180, "Express Bus"),
        ("3:00 PM", "Mumbai", 400, "Sleeper Bus"),
    ],
}

# create tool

def get_bus_details():
    res = []

    for source in buses:
        for time, destination, price, bus in buses[source]:
            res.append(
                f"From {source.title()} to {destination}, "
                f"Time: {time}, Price: Rs.{price}, Bus: {bus}"
            )

    return res


# tool schema

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_bus_details",
            "description": "Get all bus routes, timings, ticket prices and bus types",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

system_prompt = (
    "You are a travel assistant bot. "
    "Always call get_bus_details before answering questions "
    "about bus routes, timings, destinations or ticket prices. "
    "Answer in 2 or 3 short lines. "
    "Mention source, destination, time and ticket price. "
    "If the information is not available, say so."
)

user_input = input("USER : ")

messages = [
    {
        "role": "system",
        "content": system_prompt,
    },
    {
        "role": "user",
        "content": user_input,
    }
]

# tool calling loop

for _ in range(5):

    msg = client.chat.complete(
        model="mistral-small-latest",
        temperature=0.2,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response = msg.choices[0].message

    if not response.tool_calls:
        print("BOT :", response.content)
        break

    messages.append(response)

    for tc in response.tool_calls:

        if tc.function.name == "get_bus_details":
            result = get_bus_details()

        else:
            result = {
                "error": f"Unknown tool: {tc.function.name}"
            }

        messages.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tc.id,
            }
        )

else:
    print("BOT : The model kept asking for tools. Please try again.")
