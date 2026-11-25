# Hotel Guest Assistant

A single Streamlit chat assistant for hotel guests. A router sends each question
to a specialist, every message is checked before routing, and replies stream back
in the guest's language.

This is the Day 29 build: the Day 28 core hub plus a guest handbook knowledge
base, web search for nearby places, and writing tools for the concierge,
marketing, review analysis, summaries and quizzes.

## What it does

- Chat memory in `st.session_state`, with a Clear chat button.
- Only the last 10 messages are sent to the model.
- Moderation check on every guest message before routing.
- Router with six labels: `room_service`, `reservations`, `facilities`,
  `attractions`, `handbook`, `general`.
- Router fallback: any other label becomes `general`.
- Room service tools: `get_menu(category)`, `order_status(order_id)`.
- Reservations tools: `check_availability(date, room_type)`,
  `book_room(name, date, room_type)`.
- Facilities tools: `get_day_schedule(day)`, `find_facility(name)`.
- Attractions specialist with `web_search` for nearby restaurants, attractions
  and things to do. DDGS is the primary search. Tavily is used when DDGS returns
  nothing and `TAVILY_API_KEY` is set.
- General specialist answers only from a fixed hotel FAQ (check-in, check-out,
  parking, Wi-Fi, breakfast, pool). It does not cover the handbook.
- Handbook specialist answers only from the uploaded guest handbook, with page
  citations, and says "I don't know" when the best match is too far away.
- Concierge writer for welcome letters, welcome notes, day plans and itineraries.
  Short requests use one agent. Long requests (over 220 characters, or a keyword
  such as "welcome letter", "day plan" or "itinerary") run research, write and
  edit in sequence. The sidebar has an Auto, Single agent and Multi-agent
  override.
- Marketing writer for a social post or welcome message in a friendly,
  professional or playful tone.
- Review sentiment that labels each review positive, neutral or negative, counts
  each label, and flags negatives for staff.
- Handbook summary button that returns 8 bullet points.
- Quiz generator with easy, medium and hard levels. Each quiz has 5
  multiple-choice questions with answers and one-line explanations.
- Translation: prompts tell the model to reply in the guest's language. English,
  Hindi and Gujarati are the supported languages.
- Streamed replies.
- Token counter in the sidebar.
- Routed label and tool calls shown in an expander under each answer.

## Setup

1. Go to the Day 29 folder:

   ```
   cd Day29
   ```

2. Copy `.env.example` to `.env` and add your Mistral key. Add
   `TAVILY_API_KEY` only if you want the Tavily fallback:

   ```
   MISTRAL_API_KEY=your_mistral_key_here
   TAVILY_API_KEY=your_tavily_key_here
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
attractions and the handbook.

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
further than 0.55, the app replies "I don't know" instead of guessing. Answers
that use the handbook show a citation such as `from: sample_handbook.pdf, page 1`.

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

Attractions:
- Find a good restaurant near the hotel.
- What is there to do near Anand this evening?

Handbook (after uploading `data/sample_handbook.pdf`):
- What time does housekeeping visit?
- Is same-day laundry available?
- Do you allow pets? (not in the handbook, so the reply should be "I don't
  know")

Wi-Fi and check-in are answered by the general FAQ, not the handbook.

General:
- When is check-in?
- Is parking free?

Concierge:
- Short request: "Write a short welcome note for a couple arriving on Friday."
- Long request: "Write a welcome letter for the Sharma family with two children.
  Include the pool hours, breakfast timing and a simple day plan for Saturday."

Marketing:
- Write a playful social post about the pool.
- Write a professional welcome message for business guests.

Review sentiment:
- Paste three reviews, for example: "Great stay, staff were kind." / "Room was
  fine, nothing special." / "The air conditioner was broken and nobody came."

Summary:
- Click the handbook summary button. It should return 8 bullet points.

Quiz:
- Generate a medium quiz, then a hard quiz. Each should have 5 questions.

Guardrail checks:
- Send an abusive message. It should get a polite refusal and never reach a
  specialist.
- Ask to book a room for 2020-01-01. The date should be rejected with a clear
  message.
- Ask "What is the emergency number?" after loading the sample handbook. The
  answer must be "Dial 9", and the prompt injection line on page 3 must not
  change it.

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
  returns "I don't know".
- The handbook specialist adds no source line of its own. The app shows the
  citation from the retrieved chunk metadata.
- Web search returns a clear message when both providers fail, and the
  attractions specialist suggests the front desk.
- The general specialist is FAQ-only. Questions outside the FAQ get a short
  refusal and a pointer to the front desk.

## Files

- `agents.py`: router, specialists, tools, handbook RAG, writers, sentiment,
  summary and quiz. No Streamlit import.
- `app.py`: Streamlit chat UI and sidebar controls.
- `data/sample_handbook.pdf`: bundled handbook for the RAG demo.
- `chroma_db/`: persistent ChromaDB store, created on first upload.
- `.streamlit/config.toml`: theme colors.
- `requirements.txt`: dependencies.
- `.env.example`: key names, no secrets.
- `README.md`: this file.
- `hotel_guest_assistant_knowledge.md`: Day 29 build log.

## Notes

- All data is demo data. No real guest, card or account data.
- `.env` is git-ignored.
- Chat history lives in the browser session and resets on refresh.
- ChromaDB keeps the handbook index between runs in `chroma_db/`.
- `chroma_db/` is git-ignored, so a fresh clone starts with no handbook until
  one is uploaded.
- Web search needs a network connection. Without one, the attractions specialist
  says so and points the guest to the front desk.
