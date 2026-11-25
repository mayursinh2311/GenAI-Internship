import os
import sys
import json
import re
from datetime import date as date_cls

from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

# Windows console can choke on unicode such as the rupee sign
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=API_KEY) if API_KEY else None

MODEL = "mistral-small-latest"
AVAILABLE_MODELS = [
    "mistral-small-latest",
    "mistral-medium-latest",
    "mistral-large-latest",
]
MAX_TOOL_ROUNDS = 5
DAILY_TRANSFER_LIMIT = 50000.0

# Pending destructive action awaiting UI confirmation (used by the Streamlit app).
_pending_action = None


# --------------------------------
# DEMO DATA
# --------------------------------

accounts = {
    "100000001234": {"holder": "Asha Kumar", "balance": 45230.50},
    "100000005678": {"holder": "Ravi Sharma", "balance": 1200.00},
    "100000009999": {"holder": "Neha Verma", "balance": 89000.00},
}

transactions = {
    "100000001234": [
        {"date": "2026-11-18", "description": "Salary credit", "amount": 60000.00},
        {"date": "2026-11-19", "description": "Grocery store", "amount": -1200.00},
        {"date": "2026-11-20", "description": "Electricity bill", "amount": -850.50},
        {"date": "2026-11-21", "description": "Coffee shop", "amount": -180.00},
        {"date": "2026-11-22", "description": "Online shopping", "amount": -2400.00},
    ],
    "100000005678": [
        {"date": "2026-11-17", "description": "Salary credit", "amount": 35000.00},
        {"date": "2026-11-19", "description": "Rent payment", "amount": -15000.00},
        {"date": "2026-11-21", "description": "Fuel", "amount": -2200.00},
    ],
    "100000009999": [
        {"date": "2026-11-16", "description": "Freelance payment", "amount": 25000.00},
        {"date": "2026-11-20", "description": "Insurance premium", "amount": -7800.00},
    ],
}

cards = {
    "CARD1234": {"account_id": "100000001234", "status": "active"},
    "CARD5678": {"account_id": "100000005678", "status": "active"},
}

# account_id -> [date_iso, total_transferred_today]
daily_transfers = {}

bookings = {
    "BK201": "Confirmed - 2 tickets, Screen 3, 7:30 PM show",
    "BK202": "Cancelled - refund issued, reaches your account in 3-5 days",
}

menu = {
    "popcorn": 180,
    "nachos": 220,
    "coke": 120,
    "water": 40,
    "coffee": 100,
    "samosa": 60,
}


# --------------------------------
# PII MASKING
# --------------------------------

_DIGIT_RUN = re.compile(r"\b\d{9,18}\b")


def mask_account_number(value):
    """Keep only the last 4 characters and replace the rest with stars."""
    if value is None:
        return ""

    text = str(value).strip()

    if len(text) <= 4:
        return text

    return "*" * (len(text) - 4) + text[-4:]


def _mask_digit_run(match):
    value = match.group(0)
    return "*" * (len(value) - 4) + value[-4:]


def mask_text(text):
    """Mask known account ids and any long digit run in a string."""
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    for account_id in accounts:
        text = text.replace(account_id, mask_account_number(account_id))

    return _DIGIT_RUN.sub(_mask_digit_run, text)


# --------------------------------
# VALIDATION HELPERS
# --------------------------------

def _validate_account(account_id):
    """Return (account_id, None) on success or (None, message) on failure."""
    if not isinstance(account_id, str) or not account_id.strip():
        return None, "Please provide an account id."

    account_id = account_id.strip()

    if account_id not in accounts:
        return None, "Account " + mask_account_number(account_id) + " not found."

    return account_id, None


def confirm_action(prompt):
    """Ask the user for a yes/no answer. Only yes or y counts as consent."""
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        return False

    return answer.strip().lower() in {"yes", "y"}


# --------------------------------
# ACCOUNT TOOLS
# --------------------------------

def get_balance(account_id):
    account_id, error = _validate_account(account_id)
    if error:
        return error

    account = accounts[account_id]

    return (
        "Account " + mask_account_number(account_id)
        + " (" + account["holder"] + "): balance Rs "
        + f"{account['balance']:.2f}"
    )


def list_transactions(account_id, n=5):
    account_id, error = _validate_account(account_id)
    if error:
        return error

    try:
        n = int(n)
    except (TypeError, ValueError):
        return "Please provide a whole number of transactions, for example 5."

    n = max(1, min(n, 20))

    items = transactions.get(account_id, [])

    if not items:
        return "No transactions found for account " + mask_account_number(account_id) + "."

    selected = items[-n:]
    lines = [
        "Last " + str(len(selected)) + " transactions for account "
        + mask_account_number(account_id) + ":"
    ]

    for item in selected:
        amount = item["amount"]
        sign = "+" if amount >= 0 else "-"
        lines.append(
            item["date"] + " | " + item["description"] + " | "
            + sign + "Rs " + f"{abs(amount):.2f}"
        )

    return "\n".join(lines)


def block_card(card_id, confirmed=False):
    if not isinstance(card_id, str) or not card_id.strip():
        return "Please provide a card id."

    card_id = card_id.strip().upper()

    if card_id not in cards:
        return "Card " + card_id + " not found."

    card = cards[card_id]

    if card["status"] == "blocked":
        return "Card " + card_id + " is already blocked."

    if not confirmed:
        global _pending_action
        _pending_action = {"type": "block_card", "card_id": card_id}
        if not confirm_action("Confirm blocking card " + card_id + "? (yes/no): "):
            _pending_action = None
            return "Card block cancelled. Card " + card_id + " is still active."
        _pending_action = None

    card["status"] = "blocked"
    return (
        "Card " + card_id + " blocked successfully for account "
        + mask_account_number(card["account_id"]) + "."
    )


def transfer_money(from_account, to_account, amount, confirmed=False):
    from_account, error = _validate_account(from_account)
    if error:
        return error

    to_account, error = _validate_account(to_account)
    if error:
        return error

    if from_account == to_account:
        return "Choose two different accounts for a transfer."

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "Please provide a valid transfer amount."

    if amount <= 0:
        return "Transfer amount must be greater than zero."

    today = date_cls.today().isoformat()
    record = daily_transfers.get(from_account)

    if record is None or record[0] != today:
        record = [today, 0.0]
        daily_transfers[from_account] = record

    if record[1] + amount > DAILY_TRANSFER_LIMIT:
        return (
            "Daily transfer limit of Rs " + f"{DAILY_TRANSFER_LIMIT:.2f}"
            + " exceeded for account " + mask_account_number(from_account)
            + ". Already sent today: Rs " + f"{record[1]:.2f}" + "."
        )

    if accounts[from_account]["balance"] < amount:
        return "Insufficient balance in account " + mask_account_number(from_account) + "."

    if not confirmed:
        global _pending_action
        _pending_action = {
            "type": "transfer_money",
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
        }
        if not confirm_action(
            "Confirm transfer of Rs " + f"{amount:.2f}"
            + " from " + mask_account_number(from_account)
            + " to " + mask_account_number(to_account) + "? (yes/no): "
        ):
            _pending_action = None
            return "Transfer cancelled. No money was moved."
        _pending_action = None

    accounts[from_account]["balance"] -= amount
    accounts[to_account]["balance"] += amount
    record[1] += amount

    return (
        "Transferred Rs " + f"{amount:.2f}"
        + " from " + mask_account_number(from_account)
        + " to " + mask_account_number(to_account)
        + ". New balance for " + mask_account_number(from_account)
        + ": Rs " + f"{accounts[from_account]['balance']:.2f}" + "."
    )


# --------------------------------
# BOOKING AND SNACKS TOOLS
# --------------------------------

def track_booking(booking_id):
    if not isinstance(booking_id, str) or not booking_id.strip():
        return "Please provide a booking id."

    booking_id = booking_id.strip().upper()

    if booking_id in bookings:
        return bookings[booking_id]

    return "Booking " + booking_id + " not found."


def get_menu():
    lines = []
    for item, price in menu.items():
        lines.append(item + " - Rs " + str(price))
    return "\n".join(lines)


def check_price(item):
    if not isinstance(item, str) or not item.strip():
        return "Please provide a snack or drink name."

    item = item.strip().lower()

    if item in menu:
        return item + " costs Rs " + str(menu[item])

    return item + " is not on the menu."


# --------------------------------
# TOOL EXECUTOR
# --------------------------------

def parse_args(raw_args):
    if not raw_args:
        return {}

    if isinstance(raw_args, dict):
        return raw_args

    try:
        parsed = json.loads(raw_args)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def run_tool(name, args):
    args = args or {}

    try:
        if name == "get_balance":
            result = get_balance(args.get("account_id"))

        elif name == "list_transactions":
            result = list_transactions(args.get("account_id"), args.get("n", 5))

        elif name == "block_card":
            result = block_card(args.get("card_id"))

        elif name == "transfer_money":
            result = transfer_money(
                args.get("from_account"),
                args.get("to_account"),
                args.get("amount"),
            )

        elif name == "track_booking":
            result = track_booking(args.get("booking_id"))

        elif name == "get_menu":
            result = get_menu()

        elif name == "check_price":
            result = check_price(args.get("item"))

        else:
            result = "Unknown tool: " + str(name)

    except Exception as error:
        # Tool errors go back to the model so it can explain them
        result = "Tool error: " + type(error).__name__ + ": " + str(error)

    return mask_text(str(result))


# --------------------------------
# TOOL SCHEMAS
# --------------------------------

account_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get the balance of a bank account by its account id",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "12-digit account id, e.g. 100000001234",
                    }
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_transactions",
            "description": "List the most recent transactions for an account",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "12-digit account id, e.g. 100000001234",
                    },
                    "n": {
                        "type": "integer",
                        "description": "How many recent transactions to return, 1 to 20",
                    },
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "block_card",
            "description": "Block a bank card. This is a risky action and needs a yes confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "Card id, e.g. CARD1234",
                    }
                },
                "required": ["card_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_money",
            "description": (
                "Transfer money between two accounts. Needs a yes confirmation "
                "and has a daily limit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {
                        "type": "string",
                        "description": "Source account id",
                    },
                    "to_account": {
                        "type": "string",
                        "description": "Destination account id",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount in rupees",
                    },
                },
                "required": ["from_account", "to_account", "amount"],
            },
        },
    },
]

booking_tools = [
    {
        "type": "function",
        "function": {
            "name": "track_booking",
            "description": "Track a cinema booking by its id",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "e.g. BK201",
                    }
                },
                "required": ["booking_id"],
            },
        },
    }
]

snacks_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_menu",
            "description": "Get the full snacks menu with prices",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_price",
            "description": "Get the price of a snack or drink",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Snack or drink name",
                    }
                },
                "required": ["item"],
            },
        },
    },
]


# --------------------------------
# MISTRAL CALL WRAPPER
# --------------------------------

def chat(messages, tools=None, temperature=0.2, model=None):
    """Call Mistral. Return None on any network or API error."""
    if client is None:
        return None

    if model is None:
        model = MODEL

    try:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return client.chat.complete(**kwargs)

    except Exception:
        return None


# --------------------------------
# SPECIALIST AGENTS
# --------------------------------

def run_specialist(system_prompt, query, tools, model=None, temperature=0.2, trace=None):
    """Single-round specialist that can handle several tool calls in one turn."""
    if model is None:
        model = MODEL

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    response = chat(messages, tools=tools if tools else None, temperature=temperature, model=model)

    if response is None or not response.choices:
        return None

    msg = response.choices[0].message

    if msg is None:
        return None

    calls = []

    if getattr(msg, "tool_calls", None):
        messages.append(msg)

        for tool_call in msg.tool_calls:
            args = parse_args(tool_call.function.arguments)
            result = run_tool(tool_call.function.name, args)

            calls.append({
                "name": tool_call.function.name,
                "args": args,
                "result": str(result),
            })

            messages.append(
                {
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": str(result),
                    "tool_call_id": tool_call.id,
                }
            )

        final = chat(messages, temperature=temperature, model=model)

        if final is None or not final.choices:
            if trace is not None:
                trace.extend(calls)
            return None

        final_msg = final.choices[0].message

        if final_msg is None:
            if trace is not None:
                trace.extend(calls)
            return None

        content = final_msg.content
        answer = mask_text(content) if content is not None else None

        if trace is not None:
            trace.extend(calls)

        return answer

    content = msg.content
    answer = mask_text(content) if content is not None else None

    if trace is not None:
        trace.extend(calls)

    return answer


def run_account_specialist(system_prompt, query, tools, model=None, temperature=0.2, trace=None):
    """Account specialist that loops over tools until the model stops asking."""
    if model is None:
        model = MODEL

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    all_calls = []

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        response = chat(messages, tools=tools, temperature=temperature, model=model)

        if response is None or not response.choices:
            if trace is not None:
                trace.extend(all_calls)
            return None

        msg = response.choices[0].message

        if msg is None:
            if trace is not None:
                trace.extend(all_calls)
            return None

        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            content = msg.content
            answer = mask_text(content) if content is not None else None

            if trace is not None:
                trace.extend(all_calls)

            return answer

        messages.append(msg)

        for tool_call in tool_calls:
            args = parse_args(tool_call.function.arguments)
            result = run_tool(tool_call.function.name, args)

            all_calls.append({
                "name": tool_call.function.name,
                "args": args,
                "result": str(result),
            })

            messages.append(
                {
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": str(result),
                    "tool_call_id": tool_call.id,
                }
            )

    if trace is not None:
        trace.extend(all_calls)

    return mask_text(
        "I reached the maximum of " + str(MAX_TOOL_ROUNDS)
        + " tool rounds. Please try again with a simpler request."
    )


# --------------------------------
# ROUTER AGENT
# --------------------------------

VALID_LABELS = {"booking", "snacks", "account", "general"}

ROUTER_PROMPT = """
You are a query router for a customer support desk.

Reply with ONE label only, no other words:

booking - Cinema ticket, booking, show, and seat questions.
snacks  - Snacks menu and price questions.
account - Bank account questions: balance, transactions, cards, and transfers.
general - Everything else.
"""


def route(query, model=None):
    if model is None:
        model = MODEL

    messages = [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": query},
    ]

    response = chat(messages, temperature=0, model=model)

    if response is None or not response.choices:
        return None

    message = response.choices[0].message

    if message is None:
        return None

    raw = message.content or ""
    label = raw.strip().lower().strip(".!,;:")

    # Router fallback: anything that is not one of the four labels
    if label not in VALID_LABELS:
        return "general"

    return label


# --------------------------------
# SPECIALIST METADATA
# --------------------------------

SPECIALISTS = {
    "booking": {
        "system_prompt": (
            "You are a polite cinema booking support agent. "
            "Use the track_booking tool to help customers. "
            "If the tool returns an error, explain it clearly. "
            "Keep answers short and friendly."
        ),
        "tools": booking_tools,
        "runner": run_specialist,
    },
    "snacks": {
        "system_prompt": (
            "You are a friendly snacks counter assistant. "
            "Use get_menu and check_price to help customers. "
            "If the tool returns an error, explain it clearly. "
            "Keep answers short and friendly."
        ),
        "tools": snacks_tools,
        "runner": run_specialist,
    },
    "account": {
        "system_prompt": (
            "You are a helpful bank account assistant. "
            "Use get_balance(account_id), list_transactions(account_id, n), "
            "block_card(card_id), and transfer_money(from_account, to_account, amount) "
            "to help the customer. You may call several tools over several rounds. "
            "Account numbers are sensitive: never reveal a full account number, "
            "only the last 4 digits. "
            "When the customer asks to block a card or move money, call the matching "
            "tool directly. The tool itself asks for a yes confirmation in the terminal, "
            "so do not ask for confirmation in your reply. "
            "If a tool returns an error, explain it clearly instead of crashing. "
            "Keep answers short and friendly."
        ),
        "tools": account_tools,
        "runner": run_account_specialist,
    },
    "general": {
        "system_prompt": (
            "You are a helpful customer support agent. "
            "Answer the customer politely. If you do not know something, say so. "
            "Keep answers short."
        ),
        "tools": [],
        "runner": run_specialist,
    },
}


def run_for_label(label, query, model=None, trace=None):
    """Convenience: route label -> specialist call. Returns (answer, tool_calls_list)."""
    info = SPECIALISTS.get(label, SPECIALISTS["general"])
    local_trace = [] if trace is None else trace
    answer = info["runner"](
        info["system_prompt"],
        query,
        info["tools"],
        model=model,
        trace=local_trace,
    )
    return answer, local_trace
