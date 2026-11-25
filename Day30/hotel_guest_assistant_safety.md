# Day 30: Safety, quality and handoff

Date: 25 November 2026

## Goal

Add safety, quality, handoff features on top of the Day 29 Hotel Guest
Assistant. The Day 28 routing and moderation flows and the Day 29
knowledge base and writing tools must keep working unchanged.

## What I built

- Bill specialist with `get_balance(room_id)`, `list_charges(room_id)`,
  `add_charge(room_id, item, amount)` and `checkout(room_id)`.
- A tool loop capped at `MAX_TOOL_ROUNDS` (5) in `run_tool_loop` and
  `run_tool_loop_stream`. The cap is enforced with a `loop_limit` trace entry.
- A yes confirmation in code before any charge is added or a room is checked
  out. `confirm_action` defaults to False. The Streamlit app replaces it with a
  Confirm / Cancel panel stored in `st.session_state.pending_confirmation`.
  `execute_pending_action` runs the stored action after Confirm.
- PII masking. `mask_identifier` keeps the last 4 characters. `mask_text` hides
  room ids and card numbers. `normalise_room` accepts `CV-1203` or `1203`.
  `contains_card_number` blocks full card numbers typed in chat.
- Charges and check-outs are logged to `charges.csv` through `_log_row`.
- A `bill` label added to the router. `VALID_LABELS` now has seven entries.
- Web search kept from Day 29: `web_search` with `_ddgs_search` first and
  `_tavily_search` as a fallback when DDGS returns nothing and
  `TAVILY_API_KEY` is set.
- Handbook RAG kept from Day 29: `index_handbook`, `retrieve_handbook`,
  `answer_handbook`, `run_handbook_stream`, `reset_handbook`, `handbook_count`.
- Concierge writer kept from Day 29, with single and multi modes.
  `_is_long_request` uses a 220 character threshold or keywords such as
  `welcome letter`, `welcome note`, `day plan`, `itinerary`, `schedule for` and
  `plan for`. Multi mode runs research, write, edit as three calls.
- Marketing writer kept from Day 29 via `write_marketing` and
  `write_marketing_stream` for a social post or welcome message in a friendly,
  professional or playful tone.
- Review sentiment kept from Day 29 via `analyse_sentiment`, with positive,
  neutral, negative counts and a `negative_flagged` flag.
- Handbook summary kept from Day 29 via `handbook_summary` (8 bullet points) and
  quiz generator via `generate_quiz` (easy, medium, hard; 5 questions each).
- Model wrappers for Mistral and Groq. `chat` and `stream_chat` handle both
  providers. The sidebar dropdown offers Mistral models plus
  `llama-3.3-70b-versatile` on Groq.
- Groq judge via `judge_answer` and `parse_judgement`. It returns score,
  verdict, strengths, weaknesses, summary. `JUDGE_MODEL` is
  `openai/gpt-oss-20b`. Auto-judge is optional and needs `GROQ_API_KEY`.
- Staff-only CV screener via `screen_resume` and `parse_screen_result`. It
  returns `match_score`, `matched_skills`, `missing_skills`, `verdict` and
  `summary`.
- Handoff support. `wants_handoff` checks keywords such as `talk to a human`,
  `complaint` and `escalate`. `create_handoff` opens a case with an id such as
  `HO-501`, masks the room and reason, and logs to `handoffs.csv`.
  `resolve_handoff` and `open_handoffs` manage the staff queue.
- Staff dashboard helpers. `empty_usage`, `record_usage`, `record_judgement` and
  `usage_summary` count requests by label and compute the average judge score.
- Prompt injection defence in every specialist prompt through `GUARDRAIL` and the
  handbook system prompt. Handbook text and tool results are labelled as data.
- Translation rule in `LANGUAGE_RULE`, appended to the prompts. English, Hindi,
  Gujarati.
- Token counting via `estimate_tokens` and `estimate_messages_tokens`.
- Unit tests in `test_agents.py` with mocked model calls: 41 tests covering the
  router, tools, masking, loop limit, confirmation, judge parsing, screener,
  handoff, dashboard, moderation, the no-Streamlit-import rule.

## Key decisions and constants

- `MODEL = mistral-small-latest` for chat.
- `JUDGE_MODEL = openai/gpt-oss-20b` for the Groq judge.
- `GROQ_MODELS = [llama-3.3-70b-versatile]`.
- `MAX_TOOL_ROUNDS = 5`.
- `MAX_CONTEXT_MESSAGES = 10`.
- `HANDBOOK_CHUNK_SIZE = 500`.
- `HANDBOOK_CHUNK_OVERLAP = 100`.
- `HANDBOOK_DISTANCE_THRESHOLD = 0.55`.
- `HANDBOOK_COLLECTION = hotel_handbook` stored at `chroma_db/`.
- `CHARGE_LOG = charges.csv`, `HANDOFF_LOG = handoffs.csv`.
- Router temperature is 0.
- The bill specialist uses the tool loop. Other tool-using specialists use the
  single-round runner.
- `confirm_action` defaults to False so a missing confirmation never charges.
- Masking keeps the last 4 characters of room ids and card numbers.
- `_pending_action` is cleared after each confirmation attempt.

## Files changed

- `Day30/agents.py`
- `Day30/app.py`
- `Day30/test_agents.py`
- `Day30/data/sample_handbook.pdf`
- `Day30/.streamlit/config.toml`
- `Day30/requirements.txt`
- `Day30/.env.example`
- `Day30/.gitignore`
- `Day30/README.md`
- `Day30/hotel_guest_assistant_safety.md`

Generated locally and git-ignored: `Day30/chroma_db/`, `Day30/charges.csv`,
`Day30/handoffs.csv`, `Day30/.env`.

## Tests run and results

| Check | Result |
| --- | --- |
| Unit tests (mocked model calls) | Pass. 41 tests, 0 failures, 0.033s. |
| Router uses temperature 0 and falls back to general | Pass. |
| Tool loop stops at 5 rounds | Pass. |
| Bad tool JSON returns a clear error | Pass. |
| Add charge and checkout cancelled without confirmation | Pass. |
| Add charge and checkout run after confirmation | Pass. |
| Masking hides room and card numbers | Pass. |
| Judge parsing clamps score and fixes verdict | Pass. |
| CV screener parses JSON and clamps score | Pass. |
| Handoff created, masked, resolved | Pass. |
| Dashboard counts and average score | Pass. |
| Moderation blocks a threat without a model call | Pass. |
| agents.py has no Streamlit import | Pass. |

## Notes and known limits

- All data is demo data. No real guest, card or account data.
- `.env` and `chroma_db/` stay out of git.
- Chat history lives in the browser session and resets on refresh.
- ChromaDB keeps the handbook index between runs in `chroma_db/`.
- Web search needs a network connection. Without one, the attractions specialist
  says so and points the guest to the front desk.
- The Groq judge needs `GROQ_API_KEY`. Without it, the judge, Groq-hosted
  models are unavailable, and the rest of the app still works.
- The 0.55 handbook distance threshold is a demo value tuned to the bundled
  handbook, not a production cutoff.
- The concierge threshold is a simple length and keyword rule. The sidebar
  override exists so the single and multi paths can be compared directly.
- The Milvus swap from the stretch list is optional and not implemented. The
  first three stretch items (Groq model in the dropdown, distance score next to
  the citation, CSV log of confirmed charges) are implemented.