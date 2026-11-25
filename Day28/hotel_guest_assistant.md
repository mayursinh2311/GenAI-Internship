# Day 28: Core hub

Date: 24 November 2026

## Goal

Start the Hotel Guest Assistant with one Streamlit app and a separate logic
module. Day 28 covers routing, moderation, room service, reservations,
facilities and a fixed FAQ.

## What I built

- `Day28/agents.py`, a logic module with no Streamlit import.
- `Day28/app.py`, a Streamlit chat UI.
- Chat memory in `st.session_state` with a Clear chat button.
- Only the last 10 messages are sent to the model.
- Moderation on every guest message before routing.
- Router at temperature 0 with four labels: `room_service`, `reservations`,
  `facilities`, `general`.
- Router fallback: any other label becomes `general`.
- Room service tools: `get_menu(category)`, `order_status(order_id)`.
- Reservations tools: `check_availability(date, room_type)`,
  `book_room(name, date, room_type)`.
- Facilities tools: `get_day_schedule(day)`, `find_facility(name)` for the spa,
  pool and breakfast timetable.
- General specialist that answers from a fixed hotel FAQ.
- Streamed replies with `st.write_stream`.
- Token counter in the sidebar.
- Routed label and tool calls in an expander under each answer.

## Files

- `Day28/agents.py`
- `Day28/app.py`
- `Day28/.streamlit/config.toml`
- `Day28/requirements.txt`
- `Day28/.env.example`
- `Day28/.gitignore`
- `Day28/README.md`

## How to run

```
cd Day28
pip install -r requirements.txt
streamlit run app.py
```

Add `MISTRAL_API_KEY` to `Day28/.env` first.

There is also a CLI check:

```
python agents.py
```

## Done when checks

| Check | Result |
| --- | --- |
| `streamlit run app.py` starts | Pass. Health endpoint returned `ok`. |
| App renders with no exceptions | Pass. Streamlit AppTest reported no exceptions. |
| Ask for the menu | Pass. Routed to `room_service`, called `get_menu`, returned the food menu. |
| Book a room | Pass. Routed to `reservations`, called `book_room`, returned `HTL1001`. |
| Check the spa timetable | Pass. Routed to `facilities`, called `get_day_schedule`, returned Saturday spa hours. |
| Unsafe message refused | Pass. Message was blocked before routing and got a polite refusal. |
| Bad date gets a clear error | Pass. A past date returned "Date must be today or in the future." |
| Token counter updates | Pass. Sidebar showed 124 tokens after a general question, 152 after a booking question. |
| Tool arguments parse as JSON | Pass. Bad JSON returned a clear error string. |
| Last 10 messages rule | Pass. `build_messages` keeps at most 10 history messages. |

## Notes

- Moderation uses a short rules list plus one Mistral call. It only blocks when
  the model names a real safety reason, so a confused model cannot block a
  normal booking request.
- All data is demo data. No real guest, card or account data.
- `.env` stays out of git.
- This day is the base for Day 29 (handbook, web search, multi-agent, review
  sentiment, translation, summary and quiz).
