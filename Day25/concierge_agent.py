import os
import sys
import csv
import json
from datetime import datetime, date as date_cls

from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

# Windows console can choke on unicode such as the rupee sign
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

MODEL = "mistral-small-latest"
LOG_FILE = "route_log.csv"


# --------------------------------
# DEMO DATA
# --------------------------------

ROOM_TYPES = ["standard", "deluxe", "suite"]
ROOM_INVENTORY = {"standard": 5, "deluxe": 3, "suite": 2}

room_service_menu = {
    "food": {
        "club sandwich": 350,
        "pasta": 420,
        "burger": 300,
        "salad": 250,
        "soup": 180,
    },
    "drinks": {
        "coffee": 120,
        "tea": 80,
        "water": 40,
        "juice": 150,
        "soda": 100,
    },
    "amenities": {
        "extra towel": 0,
        "toothbrush kit": 50,
        "laundry service": 200,
        "iron": 0,
    },
}

orders = {
    "ORD101": "Preparing - ETA 20 minutes",
    "ORD102": "Out for delivery",
    "ORD103": "Delivered",
}

# Each booking: {"id": ..., "name": ..., "date": "YYYY-MM-DD", "room_type": ...}
reservations = []
_booking_counter = [1000]

FAQ = (
    "Check-in time: 3:00 PM. Check-out time: 11:00 AM.\n"
    "Parking: free for hotel guests.\n"
    "Wi-Fi: available throughout the hotel. Network: HotelGuest, password: HotelGuest2024.\n"
    "Breakfast: served 7:00-10:30 AM in the restaurant.\n"
    "Pool: open 6:00 AM - 10:00 PM."
)


# --------------------------------
# VALIDATION HELPERS
# --------------------------------

def validate_date(value):
    """Return (iso_date, None) on success or (None, message) on failure."""
    if not isinstance(value, str) or not value.strip():
        return None, "Please provide a date in YYYY-MM-DD format."

    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, "Invalid date. Use YYYY-MM-DD (for example 2026-12-25)."

    if parsed < date_cls.today():
        return None, "Date must be today or in the future."

    return parsed.isoformat(), None


def validate_room_type(value):
    """Return (normalized_room_type, None) or (None, message)."""
    if not isinstance(value, str) or not value.strip():
        return None, "Please provide a room type: standard, deluxe, or suite."

    room_type = value.strip().lower()

    if room_type not in ROOM_TYPES:
        return None, (
            "Unknown room type '" + value + "'. "
            "Choose from: " + ", ".join(ROOM_TYPES) + "."
        )

    return room_type, None


# --------------------------------
# TOOLS
# --------------------------------

def get_menu(category):
    if not isinstance(category, str) or not category.strip():
        return "Please provide a category: food, drinks, or amenities."

    category = category.strip().lower()

    if category not in room_service_menu:
        return (
            "Unknown category '" + category + "'. "
            "Available categories: " + ", ".join(room_service_menu) + "."
        )

    lines = []
    for item, price in room_service_menu[category].items():
        lines.append(item + " - Rs " + str(price))

    return category.title() + " menu:\n" + "\n".join(lines)


def order_status(order_id):
    if not isinstance(order_id, str) or not order_id.strip():
        return "Please provide an order id, for example ORD101."

    order_id = order_id.strip().upper()

    if order_id in orders:
        return order_id + ": " + orders[order_id]

    return "Order " + order_id + " not found."


def check_availability(date, room_type):
    date, error = validate_date(date)
    if error:
        return error

    room_type, error = validate_room_type(room_type)
    if error:
        return error

    booked = 0
    for booking in reservations:
        if booking["date"] == date and booking["room_type"] == room_type:
            booked += 1

    available = ROOM_INVENTORY[room_type] - booked

    if available <= 0:
        return "No " + room_type + " rooms available on " + date + "."

    return str(available) + " " + room_type + " room(s) available on " + date + "."


def book_room(name, date, room_type):
    if not isinstance(name, str) or not name.strip():
        return "Please provide the guest name."

    date, error = validate_date(date)
    if error:
        return error

    room_type, error = validate_room_type(room_type)
    if error:
        return error

    booked = 0
    for booking in reservations:
        if booking["date"] == date and booking["room_type"] == room_type:
            booked += 1

    if booked >= ROOM_INVENTORY[room_type]:
        return "No " + room_type + " rooms available on " + date + ". Booking not made."

    _booking_counter[0] += 1
    booking_id = "HTL" + str(_booking_counter[0])

    reservations.append(
        {
            "id": booking_id,
            "name": name.strip(),
            "date": date,
            "room_type": room_type,
        }
    )

    return (
        "Booked! Confirmation " + booking_id + ": "
        + name.strip() + ", " + room_type + " room on " + date + "."
    )


# --------------------------------
# TOOL EXECUTOR
# --------------------------------

def parse_args(raw_args):
    if not raw_args:
        return {}
    try:
        return json.loads(raw_args)
    except (json.JSONDecodeError, TypeError):
        return {}


def run_tool(name, args):
    args = args or {}

    if name == "get_menu":
        return get_menu(args.get("category"))

    elif name == "order_status":
        return order_status(args.get("order_id"))

    elif name == "check_availability":
        return check_availability(args.get("date"), args.get("room_type"))

    elif name == "book_room":
        return book_room(
            args.get("name"),
            args.get("date"),
            args.get("room_type"),
        )

    else:
        return "Unknown tool: " + str(name)


# --------------------------------
# TOOL SCHEMAS
# --------------------------------

room_service_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_menu",
            "description": "Get the room service menu for a category",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "One of: food, drinks, amenities",
                    }
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "order_status",
            "description": "Check the status of a room service order by its id",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "e.g. ORD101",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
]

reservations_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check whether a room type is available on a date",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "room_type": {
                        "type": "string",
                        "description": "One of: standard, deluxe, suite",
                    },
                },
                "required": ["date", "room_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_room",
            "description": "Book a room for a guest on a date",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Guest name",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "room_type": {
                        "type": "string",
                        "description": "One of: standard, deluxe, suite",
                    },
                },
                "required": ["name", "date", "room_type"],
            },
        },
    },
]


# --------------------------------
# MISTRAL CALL WRAPPER
# --------------------------------

def chat(messages, tools=None, temperature=0.2):
    """Call Mistral. Return None on any network or API error."""
    try:
        kwargs = {
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return client.chat.complete(**kwargs)

    except Exception as error:
        print("[API error] " + type(error).__name__ + ": " + str(error))
        return None


# --------------------------------
# SPECIALIST AGENT
# --------------------------------

def run_specialist(system_prompt, query, tools):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    response = chat(messages, tools=tools)

    if response is None or not response.choices:
        return None

    msg = response.choices[0].message

    if msg is None:
        return None

    if getattr(msg, "tool_calls", None):
        # Preserve the assistant message that contains the tool calls
        messages.append(msg)

        # A specialist may ask for more than one tool in the same turn
        for tool_call in msg.tool_calls:
            args = parse_args(tool_call.function.arguments)
            result = run_tool(tool_call.function.name, args)

            print(tool_call.function.name + " => " + str(result))

            messages.append(
                {
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": str(result),
                    "tool_call_id": tool_call.id,
                }
            )

        final = chat(messages)

        if final is None or not final.choices:
            return None

        return final.choices[0].message.content

    return msg.content


# --------------------------------
# ROUTER AGENT
# --------------------------------

VALID_LABELS = {"room_service", "reservations", "general"}

ROUTER_PROMPT = """
You are a query router for a hotel concierge.

Reply with ONE label only, no other words:

room_service - Room service menu, food or drink orders, and order status.
reservations - Room availability, room booking, and stay dates.
general      - Everything else: check-in time, parking, Wi-Fi, pool, breakfast.
"""


def route(query):
    messages = [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": query},
    ]

    response = chat(messages, temperature=0)

    if response is None or not response.choices:
        return None

    raw = response.choices[0].message.content or ""
    label = raw.strip().lower().strip(".!,;:")

    # Router fallback: anything that is not one of the three labels
    if label not in VALID_LABELS:
        return "general"

    return label


# --------------------------------
# CSV ROUTE LOG
# --------------------------------

def log_route(question, label):
    exists = os.path.exists(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if not exists:
                writer.writerow(["timestamp", "question", "label"])
            writer.writerow([datetime.now().isoformat(timespec="seconds"), question, label])
    except OSError:
        # Logging must never break the chat
        pass


# --------------------------------
# MAIN APPLICATION
# --------------------------------

def main():
    query = input("Guest: ")

    if not query.strip():
        print("Support: Please type a question about room service, reservations, or hotel info.")
        return

    label = route(query)

    if label is None:
        print("Support: Sorry, I'm having trouble connecting right now. Please try again in a moment.")
        return

    print("Routed to: " + label + " agent")
    log_route(query, label)

    if label == "room_service":
        answer = run_specialist(
            (
                "You are a polite hotel room service assistant. "
                "Use get_menu(category) and order_status(order_id) to help guests. "
                "Categories are food, drinks, and amenities. "
                "If a tool returns an error or unknown value, tell the guest clearly. "
                "Keep answers short and friendly."
            ),
            query,
            room_service_tools,
        )

    elif label == "reservations":
        answer = run_specialist(
            (
                "You are a helpful hotel reservations assistant. "
                "Use check_availability(date, room_type) when the guest asks whether a room is free. "
                "Use book_room(name, date, room_type) when the guest asks to book. "
                "When the guest gives a name, date, and room type, call book_room directly. "
                "Do not call check_availability first for a booking request. "
                "Room types are standard, deluxe, and suite. Dates use YYYY-MM-DD. "
                "If a tool returns a validation message, repeat it clearly to the guest. "
                "Never write a tool call as text; always call the tool. "
                "Keep answers short and friendly."
            ),
            query,
            reservations_tools,
        )

    else:
        answer = run_specialist(
            (
                "You are a helpful hotel concierge. Answer only from this FAQ:\n"
                + FAQ
                + "\nIf the question is outside the FAQ, politely say you cannot help "
                "and suggest contacting the front desk. Keep answers short."
            ),
            query,
            [],
        )

    if answer is None:
        print("Support: Sorry, I'm having trouble connecting right now. Please try again in a moment.")
    else:
        print("Support:", answer)


if __name__ == "__main__":
    main()
