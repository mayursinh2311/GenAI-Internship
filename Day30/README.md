# Hotel Guest Assistant

A single Streamlit chat assistant for hotel guests. A router sends each question
to a specialist, every message is checked before routing, and replies stream back
in the guest language.

This is the Day 30 build: the Day 28 core hub plus the Day 29 knowledge base,
web search, writing tools, with Day 30 safety, quality, handoff features
added on top.

## What it does

- Chat memory in `st.session_state`, with a Clear chat button.
- Only the last 10 messages are sent to the model.
- Moderation check on every guest message before routing. Blocked messages get a
  polite refusal and never reach the router.
- Router with seven labels: `room_service`, `reservations`, `bill`, `facilities`,
  `attractions`, `handbook`, `general`. Temperature 0. Any other label falls back
  to `general`.
- Room service tools: `get_menu(category)`, `order_status(order_id)`.
- Reservations tools: `check_availability(date, room_type)`,
  `book_room(name, date, room_type)`. Dates must be YYYY-MM-DD and today or later.
  Room types are standard, deluxe, suite.
- Facilities tools: `get_day_schedule(day)`, `find_facility(name)`.
- Bill tools: `get_balance(room_id)`, `list_charges(room_id)`,
  `add_charge(room_id, item, amount)`, `checkout(room_id)`. The bill specialist
  runs as a tool loop capped at 5 rounds.
- A yes confirmation in code before any charge is added or a room is checked out.
  The app shows a Confirm and Cancel panel. Nothing is written until Confirm.
- Room number and card digits are masked to the last 4 in every tool result and
  reply.
- Handbook specialist: upload a guest handbook PDF. It is split into chunks with
  page numbers and stored in ChromaDB with a persistent client. Answers come only
  from the retrieved chunks, cite `from: sample_handbook.pdf, page N`, and reply
  `I do not know` when the best match is too far away.
- Handbook constants: `HANDBOOK_CHUNK_SIZE` 500, `HANDBOOK_CHUNK_OVERLAP` 100,
  `HANDBOOK_DISTANCE_THRESHOLD` 0.55.
- Attractions specialist with `web_search`. DDGS is primary. Tavily is used when
  DDGS returns nothing and `TAVILY_API_KEY` is set.
- Concierge writer for welcome letters, welcome notes, day plans, itineraries.
  Short requests use one agent. Long requests (over 220 characters, or a keyword
  such as `welcome letter`, `day plan` or `itinerary`) run research, write, edit
  in sequence. The sidebar has an Auto, Single agent, Multi-agent
  override.
- Streaming replies.
- Tool arguments are parsed as JSON. Bad arguments return a clear error string,
  never a crash.
- Handbook text and tool results are treated as data. Every specialist prompt
  says to ignore instructions inside them (prompt injection defence).
- Translation: prompts tell the model to reply in the guest language. English,
  Hindi, Gujarati are supported.
- Token counter in the sidebar (last request and session total).
- Handbook summary button that returns 8 bullet points.
- Quiz generator with easy, medium, hard levels. Each quiz has 5
  multiple-choice questions with answers and one-line explanations.
- Marketing writer for a social post or welcome message in a friendly,
  professional or playful tone.
- Staff-only CV screener. It scores a resume against a job description and
  returns JSON with `match_score`, `matched_skills`, `missing_skills`, `verdict`
  and `summary`.
- Staff dashboard that counts requests by label, shows the average evaluator
  score, a bar chart, recent judge scores, and a Reset dashboard button.
- Review sentiment that labels each review positive, neutral, negative. Counts
  each label and flags negatives for staff.
- Single-agent mode for short answers, with the sequential pipeline for longer
  ones.
- Groq judge that scores each answer 0 to 10 with strengths and weaknesses,
  shown as JSON. `JUDGE_MODEL` is `openai/gpt-oss-20b`.
- Handoff: a guest can ask for a human. The app opens a case with an id such as
  `HO-501`, lists open cases in the staff panel with a Resolve button, and
  suggests a handoff when the judge score is low.
- Routed label and tool calls shown in an expander under each answer.

## Setup

1. Go to the Day 30 folder:

   ```
   cd Day30
   ```

2. Copy `.env.example` to `.env` and add your Mistral key. Add `GROQ_API_KEY` for
   the judge and `TAVILY_API_KEY` only if you want the Tavily fallback:

   ```
   MISTRAL_API_KEY=your_mistral_key_here
   GROQ_API_KEY=your_groq_key_here
   TAVILY_API_KEY=
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Run the app:

   ```
   streamlit run app.py
   ```

There is also a small CLI for quick checks:

```
python agents.py
```

The CLI covers routing, moderation, room service, reservations, facilities,
attractions, the handbook, and the bill.

## Loading the handbook

Use the sidebar uploader to add a guest handbook PDF. The app reads each page
with pypdf, splits it into sections by heading, caps long sections at about 500
characters with 100 characters of overlap, and stores every chunk with its file
name and page number in a persistent ChromaDB collection under `chroma_db/`.

A sample handbook is bundled at `data/sample_handbook.pdf`. Upload it from the
sidebar to try the handbook specialist. A file with the same name is not indexed
twice. Delete `chroma_db/` or upload the PDF under a new name to rebuild the
index.

Each handbook question retrieves the top 4 chunks. If the closest chunk is
further than 0.55, the app replies `I do not know` instead of guessing. Answers
that use the handbook show a citation such as `from: sample_handbook.pdf, page 1`.
The sidebar also shows the distance score next to each citation.

## Test inputs

Room service:
- Show me the food menu.
- What is the status of ORD101?

Reservations:
- Is a deluxe room free on 2026-12-25?
- Book a standard room for Asha on 2026-12-25.

Facilities:
- What time does the spa open on Saturday?
- Show me the Monday schedule.

Bill:
- What is my balance for room 1203?
- List the charges on room 1203.
- Add a 350 charge for a club sandwich to room 1203. (Confirm panel appears)
- Please check out room 1203. (Confirm panel appears)

Attractions:
- Find a good restaurant near the hotel.
- What is there to do near Anand this evening?

Handbook (after uploading `data/sample_handbook.pdf`):
- What time does housekeeping visit?
- Is same-day laundry available?
- Do you allow pets? (not in the handbook, so the reply should be `I do not know`)

Wi-Fi and check-in are answered by the general FAQ, not the handbook.

General:
- When is check-in?
- Is parking free?

Concierge:
- Short request: `Write a short welcome note for a couple arriving on Friday.`
- Long request: `Write a welcome letter for the Sharma family with two children.
  Include the pool hours, breakfast timing and a simple day plan for Saturday.`

Marketing (staff mode):
- Write a playful social post about the pool.
- Write a professional welcome message for business guests.

Review sentiment (staff mode):
- Paste three reviews, for example: `Great stay, staff were kind.` / `Room was
  fine, nothing special.` / `The air conditioner was broken and nobody came.`

Summary:
- Click the handbook summary button. It should return 8 bullet points.

Quiz:
- Generate a medium quiz, then a hard quiz. Each should have 5 questions.

CV screener (staff mode):
- Paste a resume and a job description, then click Screen resume. The result is
  JSON with a match score, matched skills, missing skills, a verdict, a summary.

Staff dashboard (staff mode):
- Open the dashboard after a few requests. It shows request counts by label, the
  average judge score, a bar chart, recent judge scores.

Handoff:
- I want to speak to a manager.

Guardrail checks:
- Send an abusive message. It should get a polite refusal and never reach a
  specialist.
- Ask to book a room for 2020-01-01. The date should be rejected with a clear
  message.
- Ask `What is the emergency number?` after loading the sample handbook. The
  answer must be `Dial 9`, and the prompt injection line on page 3 must not
  change it.
- Share a full card number in chat. The app refuses it and asks for the last 4
  digits only.

## Guardrails

- Moderation runs before routing. Blocked messages never reach the router.
- Any unknown router label falls back to `general`.
- Dates must be YYYY-MM-DD and today or later.
- Room types must be standard, deluxe or suite.
- Tool arguments are parsed as JSON. Bad arguments return a clear error string.
- Every specialist prompt says tool results are data, never instructions.
- Handbook text is passed to the model as data. Instructions inside the PDF are
  ignored. The sample handbook contains a test injection line for this.
- Handbook answers use only the retrieved chunks. A best distance above 0.55
  returns `I do not know`.
- The handbook specialist adds no source line of its own. The app shows the
  citation from the retrieved chunk metadata.
- Web search returns a clear message when both providers fail, and the
  attractions specialist suggests the front desk.
- The general specialist is FAQ-only. Questions outside the FAQ get a short
  refusal and a pointer to the front desk.
- Charges and check-outs wait for a Confirm button in code. Nothing runs
  silently.
- Room and card numbers are masked to the last 4 everywhere.
- A full card number typed in chat is refused before routing.
- The Groq judge scores answers so weak replies are visible to staff. A low
  score suggests a staff handoff.

## Unit tests

Run the offline suite (no model calls):

```
python -m unittest test_agents.py
```

The suite has 41 tests covering the router, tools, masking, the tool loop limit,
confirmation, judge parsing, the CV screener, handoff, the dashboard, moderation,
the no-Streamlit-import rule.

## Files

- `agents.py`: router, specialists, tools, handbook RAG, writers, sentiment,
  summary, quiz, judge, screener, handoff, dashboard. No Streamlit import.
- `app.py`: Streamlit chat UI and sidebar controls.
- `test_agents.py`: 41 unit tests with mocked model calls.
- `data/sample_handbook.pdf`: bundled handbook for the RAG demo.
- `chroma_db/`: persistent ChromaDB store, created on first upload.
- `.streamlit/config.toml`: theme colors.
- `requirements.txt`: dependencies.
- `.env.example`: key names, no secrets.
- `README.md`: this file.
- `hotel_guest_assistant_safety.md`: Day 30 build log.

## Notes

- All data is demo data. No real guest, card or account data.
- `.env` is git-ignored.
- Chat history lives in the browser session and resets on refresh.
- ChromaDB keeps the handbook index between runs in `chroma_db/`.
- `chroma_db/` is git-ignored, so a fresh clone starts with no handbook until
  one is uploaded.
- Web search needs a network connection. Without one, the attractions specialist
  says so and points the guest to the front desk.
- Confirmed charges are logged to `charges.csv`. Handoff cases are logged to
  `handoffs.csv`. Both are git-ignored.
- The Groq judge needs `GROQ_API_KEY`. Without it, the judge, Groq-hosted
  models are unavailable, and the rest of the app still works.
- Stretch goals: a Groq-hosted model in the sidebar dropdown, the distance score
  next to each citation, logging confirmed charges to CSV, and swapping ChromaDB
  for Milvus. The first three are already in this build; the Milvus swap remains
  optional.