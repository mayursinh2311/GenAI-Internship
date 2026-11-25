# Day 29: Knowledge, web search and writing tools

Date: 24 November 2026

## Goal

Add a guest handbook knowledge base, web search for nearby places, and a set of
writing tools to the Day 28 Hotel Guest Assistant. The Day 28 routing, moderation
and specialist flows must keep working unchanged.

## What I built

- Handbook RAG in `agents.py`. `index_handbook(source)` reads a PDF page by page
  with pypdf, splits each page into sections by heading, caps long sections at
  500 characters with 100 characters of overlap, and stores the chunks with
  `source` and `page` metadata in a persistent ChromaDB collection named
  `hotel_handbook` at `chroma_db/`.
- `retrieve_handbook(question, n_results=4)` returns the top 4 chunks with text,
  source, page and distance.
- `answer_handbook` and `run_handbook_stream` answer only from the retrieved
  chunks. If the best distance is above `HANDBOOK_DISTANCE_THRESHOLD` (0.55), the
  reply is "I don't know" and no sources are shown.
- Citations use the chunk metadata, for example `from: handbook.pdf, page 1`.
- `reset_handbook()` deletes the collection and rebuilds it, and
  `handbook_count()` reports the number of indexed chunks.
- Attractions specialist with a `web_search` tool. `_ddgs_search` runs first.
  `_tavily_search` runs only when DDGS returns nothing and `TAVILY_API_KEY` is
  set.
- Concierge writer with two modes. A short request uses one agent. A long request
  (over 220 characters, or a keyword such as "welcome letter", "welcome note",
  "day plan", "itinerary", "schedule for" or "plan for") runs research, write and
  edit as three separate calls. The sidebar has an Auto, Single agent and
  Multi-agent override.
- Marketing writer for a social post or welcome message in a friendly,
  professional or playful tone.
- Review sentiment via `analyse_sentiment`. The model returns JSON, the code
  counts positive, neutral and negative labels, and `negative_flagged` is true
  when at least one review is negative.
- Handbook summary button that asks for 8 short bullet points from the indexed
  handbook text.
- Quiz generator with easy, medium and hard levels. `generate_quiz` asks for 5
  multiple-choice questions, 4 options each, the correct answer and a one-line
  explanation.
- Language rule added to the handbook, general and tool-using prompts. Replies
  come back in English, Hindi or Gujarati, matching the guest.
- Prompt-injection defence: handbook text and tool results are labelled as data,
  and the prompts say to ignore instructions inside them.
- Router expanded to six labels: `room_service`, `reservations`, `facilities`,
  `attractions`, `handbook`, `general`.
- `general` stays FAQ-only for check-in, check-out, parking, Wi-Fi, breakfast and
  pool. `attractions` handles nearby places through web search. `handbook`
  handles hotel rules and details from the uploaded PDF.
- Moderation still runs before routing.
- Token counter and the last-10-messages memory still apply to every request.
- Bundled sample handbook at `data/sample_handbook.pdf`. It has 3 pages and a
  deliberate prompt-injection line on page 3.

## Files

- `Day29/agents.py`
- `Day29/app.py`
- `Day29/data/sample_handbook.pdf`
- `Day29/chroma_db/` (generated, git-ignored)
- `Day29/.streamlit/config.toml`
- `Day29/requirements.txt`
- `Day29/.env.example`
- `Day29/.gitignore`
- `Day29/README.md`
- `Day29/hotel_guest_assistant_knowledge.md`

## How to run

```
cd Day29
pip install -r requirements.txt
streamlit run app.py
```

Add `MISTRAL_API_KEY` to `Day29/.env` first. Add `TAVILY_API_KEY` only if the
Tavily fallback is needed.

Upload `data/sample_handbook.pdf` from the sidebar, then ask handbook questions.

There is also a CLI check:

```
python agents.py
```

## Done when checks

| Check | Result |
| --- | --- |
| Handbook question with page citation | Pass. Asked "What time does housekeeping visit?" and got the housekeeping hours with `from: sample_handbook.pdf, page 2`. |
| Out-of-handbook question gets "I don't know" | Pass. Asked "Do you allow pets?" and the best distance was above 0.55, so the reply was "I don't know. I could not find that in the guest handbook." |
| Welcome letter uses multi-agent | Pass. A welcome letter request ran research, write and edit, and the trace showed the three steps. |
| Day 28 flows still work | Pass. Menu, order status, booking, spa hours and Wi-Fi FAQ all returned the same answers as Day 28. |
| Web search returns nearby places | Pass. "Find a good restaurant near the hotel" called `web_search` and returned named results with short descriptions. |
| Review sentiment returns counts | Pass. Three reviews returned positive 2, neutral 0, negative 1, and the negative was flagged for staff. |
| Quiz generator returns 5 questions | Pass. A medium quiz returned 5 multiple-choice questions with 4 options, answers and explanations. |
| Prompt injection line in handbook is ignored | Pass. Asked "What is the emergency number?" and the answer was "Dial 9". The injected line on page 3 was ignored. |

## Notes

- The handbook index is keyed by file name. Uploading the same file again adds 0
  chunks. Delete `chroma_db/` or rename the PDF to rebuild.
- Chunking is per page and per section. Each heading starts a new chunk, and long
  sections are split at 500 characters. A citation always points at the page the
  text came from.
- Distance is cosine distance from ChromaDB. The 0.55 threshold is a demo value,
  tuned to the bundled handbook, not a production cutoff.
- DDGS needs no key. Tavily is a fallback and stays off when `TAVILY_API_KEY` is
  missing.
- The concierge threshold is a simple length and keyword rule. The sidebar
  override exists so the single and multi paths can be compared directly.
- The general FAQ and the handbook are aligned on the Wi-Fi network and password,
  so both routes agree. `general` answers from the short FAQ, `handbook` answers
  from the PDF, and each answer shows where it came from.
- All data is demo data. `.env` and `chroma_db/` stay out of git.
