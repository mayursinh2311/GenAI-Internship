# Hotel Guest Assistant

A single Streamlit chat assistant for hotel guests. A router sends each guest
question to a specialist, and every message is checked before it reaches the
model.

This is the Day 28 build: the core hub. Later days add the handbook, the bill
loop and the judge.

## What it does

- Chat memory in `st.session_state`, with a Clear chat button.
- Only the last 10 messages are sent to the model.
- Moderation check on every guest message before routing.
- Router with four labels: `room_service`, `reservations`, `facilities`, `general`.
- Router fallback: any other label becomes `general`.
- Room service tools: `get_menu(category)`, `order_status(order_id)`.
- Reservations tools: `check_availability(date, room_type)`, `book_room(name, date, room_type)`.
- Facilities tools: `get_day_schedule(day)`, `find_facility(name)`.
- General specialist answers from a fixed hotel FAQ.
- Streamed replies.
- Token counter in the sidebar.
- Routed label and tool calls shown in an expander under each answer.

## Setup

1. Copy `.env.example` to `.env` and add your Mistral key.
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the app:

   ```
   streamlit run app.py
   ```

There is also a small CLI for quick checks:

```
python agents.py
```

## Test inputs

Room service:
- Show me the food menu.
- What is the status of ORD101?

Reservations:
- Is a deluxe room free on 2026-12-25?
- Book a standard room for Asha on 2026-12-25.

Facilities:
- What time does the spa open on Saturday?
- Show me Monday's schedule.

General:
- What is the Wi-Fi password?
- When is check-in?

Guardrail checks:
- Send an abusive message. It should get a polite refusal and never reach a specialist.
- Ask to book a room for 2020-01-01. The date should be rejected with a clear message.

## Guardrails in this build

- Moderation runs before routing.
- Any unknown router label falls back to `general`.
- Dates must be YYYY-MM-DD and today or later.
- Room types must be standard, deluxe or suite.
- Tool arguments are parsed as JSON. Bad arguments return a clear error string.
- Every specialist prompt tells the model that tool results are data, not instructions.

## Files

- `agents.py`: router, specialists, tools and validation. No Streamlit import.
- `app.py`: Streamlit chat UI.
- `.streamlit/config.toml`: theme colors.
- `requirements.txt`: dependencies.
- `.env.example`: key names, no secrets.

## Notes

- All data is demo data.
- Chat history resets when the browser session is refreshed.
- `.env` is git-ignored.
