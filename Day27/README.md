# Day 27: Streamlit support dashboard with chat memory

A Streamlit web app for support staff. Customer questions go through the same router
and specialists as Day 26 (cinema booking, snacks, bank account, general), but in a
browser chat UI with history, routed labels, tool calls, and a model dropdown.

## How it works

1. Staff type a question in the chat box.
2. A router call (temperature 0) replies with one label: `booking`, `snacks`,
   `account`, or `general`.
3. The matching specialist answers, possibly calling tools.
4. Each answer shows the routed label and the tool calls in an expandable section.
5. History is kept in `st.session_state` for the browser session and resets on refresh.

## Files

- `agents.py`: router, specialists, tools, validation, masking, and the Mistral wrapper. No Streamlit dependency.
- `app.py`: Streamlit UI (chat, sidebar, expanders, feedback).
- `tests.py`: unit tests that mock the Mistral call (no API key needed).
- `requirements.txt`: the Python packages you need.
- `.env.example`: the key the app expects.

## Setup

Install the packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file in this folder:

```
MISTRAL_API_KEY=your_mistral_key_here
```

Or add `MISTRAL_API_KEY` to Streamlit secrets.

## Run

```bash
streamlit run app.py
```

## Run the tests

The tests mock the Mistral call, so they do not need an API key.

```bash
python tests.py
```

## Test inputs

Booking:

- Where is my booking BK201?

Snacks:

- How much is popcorn?

Account:

- What is my balance for account 100000001234?
- Show the last 3 transactions for account 100000001234.

General:

- What are your support hours?

## Notes

- Agent code is separated from the UI, so it can be tested without Streamlit running.
- The routed label and tool calls appear under each answer in an expandable section.
- The sidebar has a model dropdown and a clear-chat button.
- History lasts for the browser session and resets on refresh.
- Destructive actions (block card, transfer) use a terminal yes/no confirmation;
  in the web app they cancel safely when no terminal is available.
- Feedback buttons under each answer save to `feedback.csv` (stretch).
- A booking confirmation can be pasted into the sidebar and attached to the next question (stretch).
- `.env` holds the real key. It is ignored by git.
