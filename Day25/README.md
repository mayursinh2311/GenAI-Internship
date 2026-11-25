# Day 25: Hotel concierge with a router and three specialists

A CLI chatbot for hotel guests, built on Mistral. A router reads the guest question and sends it to
one specialist: room service, reservations, or general.

## How it works

1. You type a question such as "What's on the drinks menu?" or "Book a deluxe room for Asha on 2026-12-25".
2. A router call (temperature 0) replies with one label: `room_service`, `reservations`, or `general`.
3. The matching specialist answers:
   - **room_service**: has `get_menu(category)` and `order_status(order_id)`.
   - **reservations**: has `check_availability(date, room_type)` and `book_room(name, date, room_type)`.
   - **general**: no tools, answers from a fixed FAQ (check-in time, parking, Wi-Fi, breakfast, pool).
4. Each tool call is printed as `tool_name => result`, then the final answer is printed after `Support:`.

The router falls back to `general` when the model replies with anything other than the three labels.

## Demo data

- Room service menu: `food`, `drinks`, and `amenities` categories with rupee prices.
- Orders: `ORD101` (preparing), `ORD102` (out for delivery), `ORD103` (delivered).
- Rooms: `standard` (5), `deluxe` (3), `suite` (2) per date.
- Dates must use `YYYY-MM-DD` and must be today or later.

## Files

- `concierge_agent.py`: router, specialists, tools, validation, and the CLI.
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

## Run

```bash
python concierge_agent.py
```

## Test inputs

Room service:

- What's on the drinks menu?
- Status of order ORD101?

Reservations:

- Is a deluxe room available on 2026-12-25?
- Book a standard room for John on 2026-12-24.

Validation:

- Book a suite on 2026-13-40. (bad date)
- Check availability of a penthouse on 2026-12-25. (unknown room type)

General:

- What time is check-in?
- Do you have free parking?
- What's the Wi-Fi password?

Fallback:

- What's the weather today?

## Notes

- Bad dates and unknown room types return a clear message. The app does not crash.
- Network or rate-limit errors print a friendly retry message.
- Each question and its routed label are appended to `route_log.csv`.
- A specialist can call two tools in one turn. The results are combined in the final answer.
- `.env` holds the real key. It is ignored by git.
