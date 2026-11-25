"""Streamlit UI for the Hotel Guest Assistant (Day 30).

The app keeps chat memory in st.session_state, moderates each message, routes it
to a specialist, a handbook search, the bill loop or the concierge, and streams
the answer. Charges and check-outs wait for a Confirm button. The sidebar also
carries the handbook tools, the staff dashboard, the CV screener, the Groq judge
and the handoff queue. All agent logic lives in agents.py.
"""

import re

import streamlit as st

import agents

st.set_page_config(
    page_title="Hotel Guest Assistant",
    page_icon="H",
    layout="centered",
)

# Calm, neutral shell. Keep the accent to a single deep green.
st.markdown(
    """
    <style>
      .block-container { max-width: 820px; padding-top: 2.2rem; }
      [data-testid="stSidebar"] { background: #f3f4f1; }
      h1 { letter-spacing: -0.02em; }
      [data-testid="stChatMessage"] { border-radius: 14px; }
      [data-testid="stMetricValue"] { font-size: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Hotel Guest Assistant")
st.caption(
    "Room service, reservations, the bill, facilities, the guest handbook, "
    "web search and staff tools. Powered by Mistral, with a Groq judge."
)

if agents.client is None:
    st.error("MISTRAL_API_KEY is missing. Add it to Day30/.env and reload.")
    st.stop()


# --------------------------------
# SESSION STATE
# --------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_request_tokens" not in st.session_state:
    st.session_state.last_request_tokens = 0

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

if "marketing_output" not in st.session_state:
    st.session_state.marketing_output = ""

if "sentiment_result" not in st.session_state:
    st.session_state.sentiment_result = None

if "handbook_summary_output" not in st.session_state:
    st.session_state.handbook_summary_output = ""

if "quiz_output" not in st.session_state:
    st.session_state.quiz_output = ""

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None

if "usage" not in st.session_state:
    st.session_state.usage = agents.empty_usage()

if "screen_result" not in st.session_state:
    st.session_state.screen_result = None

CONCIERGE_MODE_LABELS = {
    "Auto": "auto",
    "Single agent": "single",
    "Multi-agent": "multi",
}

CONCIERGE_SYSTEM_PROMPT = (
    "You are a hotel concierge writer. Draft the requested welcome letter or "
    "day plan from hotel demo details only. Keep it warm, clear and ready to send."
)


def _streamlit_confirm(prompt, action=None):
    """Replace the safe default so the guest sees a Confirm panel."""
    st.session_state.pending_confirmation = {
        "prompt": prompt,
        "action": action,
    }
    return False


agents.confirm_action = _streamlit_confirm


def _find_question(index):
    """Return the guest message that came before this assistant message."""
    for position in range(index - 1, -1, -1):
        message = st.session_state.messages[position]
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _run_judge(message, question):
    """Score one answer with the Groq judge and store the result."""
    result = agents.judge_answer(question, message.get("content", ""))

    if isinstance(result.get("score"), int):
        agents.record_judgement(st.session_state.usage, question, result)

    message["judge"] = result
    return result


def _add_assistant(content, label, trace=None, tokens=0, sources=None, judge=None):
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": content,
            "label": label,
            "tool_calls": trace or [],
            "tokens": tokens,
            "sources": sources or [],
            "judge": judge,
        }
    )
    agents.record_usage(st.session_state.usage, label)


def _show_sources(sources):
    for source in sources:
        line = (
            "from: " + str(source.get("source", "handbook.pdf"))
            + ", page " + str(source.get("page", 0))
        )
        distance = source.get("distance")
        if distance is not None:
            line += " (distance " + str(round(distance, 3)) + ")"
        st.caption(line)


_MASKED_ID = re.compile(r"\*{3,}\d{4}")


def _display(text):
    """Escape mask stars so Markdown does not turn them into bold text."""
    return _MASKED_ID.sub(
        lambda match: match.group(0).replace("*", "\\*"),
        str(text or ""),
    )


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:
    st.header("Guest controls")

    model = st.selectbox(
        "Model",
        agents.AVAILABLE_MODELS,
        index=0,
        format_func=lambda name: name + (" (Groq)" if agents.is_groq_model(name) else ""),
    )

    if agents.is_groq_model(model) and agents.groq_client is None:
        st.warning("GROQ_API_KEY is missing, so this model will not answer. Add it to Day30/.env.")

    mode_label = st.radio(
        "Concierge mode",
        list(CONCIERGE_MODE_LABELS.keys()),
        index=0,
    )
    concierge_mode = CONCIERGE_MODE_LABELS[mode_label]

    auto_judge = st.checkbox("Auto-judge answers (Groq)")

    if auto_judge and not agents.judge_available():
        st.warning("GROQ_API_KEY is missing, so the judge is off.")

    st.metric(
        "Tokens sent (last request)",
        st.session_state.last_request_tokens,
    )
    st.caption("Session total: about " + str(st.session_state.total_tokens) + " tokens")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_confirmation = None
        st.session_state.last_request_tokens = 0
        st.session_state.total_tokens = 0
        st.rerun()

    st.divider()
    st.header("Guest handbook")

    uploaded = st.file_uploader("Upload the guest handbook PDF", type=["pdf"])

    if uploaded is not None:
        if st.button("Index handbook", use_container_width=True):
            with st.spinner("Indexing the handbook..."):
                new_chunks = agents.index_handbook(uploaded)

            if new_chunks == 0:
                st.info("Already indexed")
            else:
                st.success("Indexed " + str(new_chunks) + " chunks")

    if st.button("Reset handbook", use_container_width=True):
        agents.reset_handbook()
        st.info("Handbook cleared")

    st.caption("Chunks indexed: " + str(agents.handbook_count()))

    if st.button("Summarize handbook", use_container_width=True):
        with st.spinner("Summarizing the handbook..."):
            summary = agents.handbook_summary(model=model)

        if summary is None:
            summary = "Could not summarize the handbook right now. Please try again."

        st.session_state.handbook_summary_output = summary

    if st.session_state.handbook_summary_output:
        st.markdown(st.session_state.handbook_summary_output)

    quiz_level = st.selectbox("Quiz level", ["easy", "medium", "hard"])

    if st.button("Generate quiz", use_container_width=True):
        with st.spinner("Writing the quiz..."):
            quiz = agents.generate_quiz(quiz_level, model=model)

        if quiz is None:
            quiz = "Could not generate a quiz right now. Please try again."

        st.session_state.quiz_output = quiz

    if st.session_state.quiz_output:
        st.markdown(st.session_state.quiz_output)

    st.divider()
    staff_mode = st.checkbox("Staff mode")

    if staff_mode:
        st.header("Marketing writer")

        marketing_kind = st.selectbox("Kind", ["social post", "welcome message"])
        marketing_tone = st.selectbox("Tone", ["friendly", "professional", "playful"])
        marketing_topic = st.text_input("Topic")

        marketing_written = False
        if st.button("Write", use_container_width=True):
            if not marketing_topic.strip():
                st.warning("Add a topic first.")
            else:
                written = st.write_stream(
                    agents.write_marketing_stream(
                        marketing_kind,
                        marketing_topic,
                        marketing_tone,
                        model=model,
                    )
                )

                if not isinstance(written, str):
                    written = "".join(str(part) for part in written)

                st.session_state.marketing_output = written
                marketing_written = True

        if st.session_state.marketing_output and not marketing_written:
            st.markdown(st.session_state.marketing_output)

        st.header("Review sentiment")

        reviews_text = st.text_area("Reviews, one per line", height=130)

        if st.button("Analyse reviews", use_container_width=True):
            if not reviews_text.strip():
                st.warning("Paste at least one review first.")
            else:
                with st.spinner("Analysing the reviews..."):
                    st.session_state.sentiment_result = agents.analyse_sentiment(
                        reviews_text,
                        model=model,
                    )

        sentiment = st.session_state.sentiment_result
        if sentiment:
            if sentiment.get("error"):
                st.error(sentiment["error"])
            else:
                counts = sentiment.get("counts") or {}
                st.write(
                    "Positive: " + str(counts.get("positive", 0))
                    + " | Neutral: " + str(counts.get("neutral", 0))
                    + " | Negative: " + str(counts.get("negative", 0))
                )

                if sentiment.get("summary"):
                    st.caption(sentiment["summary"])

                if sentiment.get("negative_flagged"):
                    st.warning("Negative reviews found. A reply is recommended.")

                for review in sentiment.get("reviews") or []:
                    st.write("- " + review.get("label", "neutral") + ": " + review.get("text", ""))

        st.header("CV screener")

        resume_text = st.text_area("Resume", height=140, key="cv_resume")
        job_text = st.text_area("Job description", height=120, key="cv_job")

        if st.button("Screen resume", use_container_width=True):
            if not resume_text.strip() or not job_text.strip():
                st.warning("Paste a resume and a job description first.")
            else:
                with st.spinner("Screening the resume..."):
                    st.session_state.screen_result = agents.screen_resume(
                        resume_text,
                        job_text,
                        model=model,
                    )

        screen = st.session_state.screen_result
        if screen:
            if screen.get("error"):
                st.error(screen["error"])
            else:
                st.metric("Match score", str(screen.get("match_score", 0)) + " / 100")
                st.caption("Verdict: " + str(screen.get("verdict", "")))
                st.write("Matched: " + ", ".join(screen.get("matched_skills") or []))
                st.write("Missing: " + ", ".join(screen.get("missing_skills") or []))
                if screen.get("summary"):
                    st.caption(screen["summary"])
                st.json(screen)

        st.header("Dashboard")

        summary = agents.usage_summary(st.session_state.usage)
        metric_cols = st.columns(2)
        metric_cols[0].metric("Requests", summary["total"])
        metric_cols[1].metric(
            "Average judge score",
            "n/a" if summary["average_score"] is None else summary["average_score"],
        )

        if summary["by_label"]:
            st.bar_chart(summary["by_label"])
        else:
            st.caption("No requests yet.")

        judged = st.session_state.usage.get("judged") or []
        if judged:
            st.caption("Recent judge scores")
            for item in reversed(judged[-5:]):
                st.write(
                    str(item.get("score")) + " / 10 - " + str(item.get("verdict"))
                    + ": " + str(item.get("question", ""))[:70]
                )

        if st.button("Reset dashboard", use_container_width=True):
            st.session_state.usage = agents.empty_usage()
            st.rerun()

        st.header("Handoffs")

        cases = agents.open_handoffs()
        if not cases:
            st.caption("No open handoffs.")

        for case in cases:
            st.write("**" + case["id"] + "** | " + case["created"])
            st.caption(case.get("reason", ""))
            if case.get("room"):
                st.caption("Room " + _display(case["room"]))

            if st.button("Resolve " + case["id"], key="resolve_" + case["id"]):
                agents.resolve_handoff(case["id"])
                st.rerun()

    st.divider()
    st.write("Try asking:")
    st.caption("What is my balance for room 1203?")
    st.caption("Add a 350 charge for a club sandwich to room 1203.")
    st.caption("Please check out room 1203.")
    st.caption("What does the guest handbook say about late check-out?")
    st.caption("What restaurants are near the hotel?")
    st.caption("I want to speak to a manager.")

    st.divider()
    st.caption("History lives in this browser session and resets on refresh.")


# --------------------------------
# PENDING CONFIRMATION
# --------------------------------

pending = st.session_state.pending_confirmation

if pending and pending.get("action"):
    st.warning(_display(pending["prompt"]))
    confirm_col, cancel_col = st.columns(2)

    if confirm_col.button("Confirm", type="primary", use_container_width=True):
        result = agents.execute_pending_action(pending["action"])
        st.session_state.pending_confirmation = None
        _add_assistant(result, "bill")
        st.rerun()

    if cancel_col.button("Cancel", use_container_width=True):
        st.session_state.pending_confirmation = None
        st.info("Cancelled. Nothing was changed.")
        st.rerun()


# --------------------------------
# RENDER HISTORY
# --------------------------------

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(_display(message["content"]))

        if message["role"] != "assistant":
            continue

        label = message.get("label")
        tool_calls = message.get("tool_calls") or []

        with st.expander("Routed label and tool calls", expanded=False):
            st.write("Routed to: **" + (label or "unknown") + "**")
            if tool_calls:
                for call in tool_calls:
                    st.write("- `" + str(call.get("name")) + "` " + str(call.get("args", {})))
                    st.write("  => " + str(call.get("result", "")))
            else:
                st.write("No tool calls.")

        _show_sources(message.get("sources") or [])

        if message.get("tokens"):
            st.caption("About " + str(message["tokens"]) + " tokens sent")

        judge = message.get("judge")
        if judge:
            st.json(judge)
            if isinstance(judge.get("score"), int) and judge["score"] <= 3:
                st.warning("Low score. Consider a staff handoff.")

        action_cols = st.columns(2)

        if agents.judge_available() and not judge:
            if action_cols[0].button("Judge this answer", key="judge_" + str(index)):
                with st.spinner("Scoring the answer..."):
                    _run_judge(message, _find_question(index))
                st.rerun()

        if action_cols[1].button("Flag for staff", key="flag_" + str(index)):
            case = agents.create_handoff(
                "Staff review requested for an answer.",
                score=(judge or {}).get("score"),
            )
            st.success("Handoff " + case["id"] + " created.")


# --------------------------------
# NEW INPUT
# --------------------------------

prompt = st.chat_input("Ask about the hotel, your bill, the handbook or the local area...")

if prompt:
    shown_prompt = agents.mask_text(prompt) if agents.contains_card_number(prompt) else prompt
    st.session_state.messages.append({"role": "user", "content": shown_prompt})
    with st.chat_message("user"):
        st.write(shown_prompt)

    # 1. Card safety gate: never accept a full card number in chat.
    if agents.contains_card_number(prompt):
        refusal = (
            "Please do not share a full card number in chat. "
            "I only need the last 4 digits, or you can settle at the front desk."
        )
        with st.chat_message("assistant"):
            st.write(refusal)
        _add_assistant(refusal, "security")
        st.stop()

    # 2. Handoff gate: a clear request for a person opens a staff case.
    if agents.wants_handoff(prompt):
        match = re.search(r"\b(?:CV-)?\d{4}\b", prompt, re.IGNORECASE)
        room_id = match.group(0) if match else None
        case = agents.create_handoff(prompt, room_id=room_id)

        answer = (
            "I have passed this to the front desk as case " + case["id"] + ". "
            "A staff member will follow up. You can also dial 0 from your room."
        )

        with st.chat_message("assistant"):
            st.write(answer)

        _add_assistant(answer, "handoff")
        st.stop()

    # 3. Moderation gate: blocked messages never reach the router.
    check = agents.moderate(prompt)
    if not check["allowed"]:
        refusal = (
            "I am sorry, I cannot help with that. "
            "Please keep messages respectful so I can assist with your stay."
        )
        with st.chat_message("assistant"):
            st.write(refusal)
        _add_assistant(refusal, "moderation")
        st.stop()

    # 4. Pick the path: concierge for long requests, otherwise route a label.
    if agents._is_long_request(prompt):
        label = "concierge"
    else:
        label = agents.route(prompt, model=model) or "general"

    history = st.session_state.messages[-agents.MAX_CONTEXT_MESSAGES:]

    # 5. Token estimate for the request that is about to go out.
    if label == "concierge":
        system_prompt = CONCIERGE_SYSTEM_PROMPT
    elif label == "handbook":
        matches = agents.retrieve_handbook(prompt)
        system_prompt = (
            agents.HANDBOOK_SYSTEM_PROMPT
            + "\n\nHandbook context:\n"
            + agents._handbook_context(matches)
        )
    else:
        system_prompt = agents.SPECIALISTS.get(label, agents.SPECIALISTS["general"])["system_prompt"]

    request_messages = agents.build_messages(system_prompt, prompt, history)
    tokens = agents.estimate_messages_tokens(request_messages)

    st.session_state.last_request_tokens = tokens
    st.session_state.total_tokens += tokens

    # 6. Stream the answer and keep the trace for the expander.
    trace = []

    with st.chat_message("assistant"):
        if label == "concierge":
            stream = agents.run_concierge_stream(
                prompt,
                mode=concierge_mode,
                model=model,
                trace=trace,
            )
        elif label == "handbook":
            stream = agents.run_handbook_stream(
                prompt,
                model=model,
                trace=trace,
                history=history,
            )
        elif label == "bill":
            stream = agents.run_tool_loop_stream(
                agents.BILL_SYSTEM_PROMPT,
                prompt,
                agents.bill_tools,
                model=model,
                trace=trace,
                history=history,
            )
        else:
            info = agents.SPECIALISTS.get(label, agents.SPECIALISTS["general"])
            stream = agents.run_specialist_stream(
                info["system_prompt"],
                prompt,
                info["tools"],
                model=model,
                trace=trace,
                history=history,
            )

        answer = st.write_stream(stream) if label != "bill" else None

        if label == "bill":
            answer = "".join(str(part) for part in stream)

            if st.session_state.pending_confirmation:
                answer = (
                    "This action is waiting for your confirmation. "
                    "Nothing has been changed yet. Use the Confirm or Cancel buttons above."
                )

            st.markdown(_display(answer))

        if answer is None:
            answer = ""
        elif not isinstance(answer, str):
            answer = "".join(str(part) for part in answer)

        answer = agents.mask_text(answer)

        if not answer:
            answer = "Sorry, I am having trouble connecting right now. Please try again in a moment."

        sources = []
        for call in trace:
            for source in call.get("sources") or []:
                sources.append(source)

        _show_sources(sources)

        if tokens:
            st.caption("About " + str(tokens) + " tokens sent")

        judge = None
        if auto_judge and agents.judge_available() and answer:
            with st.spinner("Scoring the answer..."):
                judge = agents.judge_answer(prompt, answer)

            if isinstance(judge.get("score"), int):
                agents.record_judgement(st.session_state.usage, prompt, judge)

            st.json(judge)

    _add_assistant(answer, label, trace=trace, tokens=tokens, sources=sources, judge=judge)

    if st.session_state.pending_confirmation:
        st.rerun()
