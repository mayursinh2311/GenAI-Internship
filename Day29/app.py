"""Streamlit UI for the Hotel Guest Assistant (Day 29).

The app keeps chat memory in st.session_state, moderates each message, routes it
to a specialist, a handbook search or the concierge, and streams the answer.
The sidebar also carries the guest handbook tools and the staff tools. All agent
logic lives in agents.py.
"""

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
    "Room service, reservations, facilities, the guest handbook, web search "
    "and staff tools. Powered by Mistral."
)

if agents.client is None:
    st.error("MISTRAL_API_KEY is missing. Add it to Day29/.env and reload.")
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

CONCIERGE_MODE_LABELS = {
    "Auto": "auto",
    "Single agent": "single",
    "Multi-agent": "multi",
}

CONCIERGE_SYSTEM_PROMPT = (
    "You are a hotel concierge writer. Draft the requested welcome letter or "
    "day plan from hotel demo details only. Keep it warm, clear and ready to send."
)


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:
    st.header("Guest controls")

    model = st.selectbox("Model", agents.AVAILABLE_MODELS, index=0)

    mode_label = st.radio(
        "Concierge mode",
        list(CONCIERGE_MODE_LABELS.keys()),
        index=0,
    )
    concierge_mode = CONCIERGE_MODE_LABELS[mode_label]

    st.metric(
        "Tokens sent (last request)",
        st.session_state.last_request_tokens,
    )
    st.caption("Session total: about " + str(st.session_state.total_tokens) + " tokens")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
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

    st.divider()
    st.write("Try asking:")
    st.caption("What does the guest handbook say about late check-out?")
    st.caption("What restaurants are near the hotel?")
    st.caption("What time does the spa open on Saturday?")
    st.caption("Show me the food menu.")
    st.caption("Book a standard room for Asha on 2026-12-25.")

    st.divider()
    st.caption("History lives in this browser session and resets on refresh.")


# --------------------------------
# RENDER HISTORY
# --------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant":
            label = message.get("label")
            tool_calls = message.get("tool_calls") or []

            with st.expander("Routed label and tool calls", expanded=False):
                st.write("Routed to: **" + (label or "unknown") + "**")
                if tool_calls:
                    for call in tool_calls:
                        st.write("- `" + call["name"] + "` " + str(call.get("args", {})))
                        st.write("  => " + str(call.get("result", "")))
                else:
                    st.write("No tool calls.")

            for source in message.get("sources") or []:
                line = (
                    "from: " + str(source.get("source", "handbook.pdf"))
                    + ", page " + str(source.get("page", 0))
                )
                distance = source.get("distance")
                if distance is not None:
                    line += " (distance " + str(round(distance, 3)) + ")"
                st.caption(line)

            if message.get("tokens"):
                st.caption("About " + str(message["tokens"]) + " tokens sent")


# --------------------------------
# NEW INPUT
# --------------------------------

prompt = st.chat_input("Ask about the hotel, the handbook or the local area...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 1. Moderation gate: blocked messages never reach the router.
    check = agents.moderate(prompt)
    if not check["allowed"]:
        refusal = (
            "I am sorry, I cannot help with that. "
            "Please keep messages respectful so I can assist with your stay."
        )
        with st.chat_message("assistant"):
            st.write(refusal)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": refusal,
                "label": "moderation",
                "tool_calls": [],
                "tokens": 0,
                "sources": [],
            }
        )
        st.stop()

    # 2. Pick the path: concierge for long requests, otherwise route a label.
    if agents._is_long_request(prompt):
        label = "concierge"
    else:
        label = agents.route(prompt, model=model) or "general"

    history = st.session_state.messages[-agents.MAX_CONTEXT_MESSAGES:]

    # 3. Token estimate for the request that is about to go out.
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

    # 4. Stream the answer and keep the trace for the expander.
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

        answer = st.write_stream(stream)

        if not isinstance(answer, str):
            answer = "".join(str(part) for part in answer)

        if not answer:
            answer = "Sorry, I am having trouble connecting right now. Please try again in a moment."

        sources = []
        for call in trace:
            for source in call.get("sources") or []:
                sources.append(source)

        for source in sources:
            line = (
                "from: " + str(source.get("source", "handbook.pdf"))
                + ", page " + str(source.get("page", 0))
            )
            distance = source.get("distance")
            if distance is not None:
                line += " (distance " + str(round(distance, 3)) + ")"
            st.caption(line)

        if tokens:
            st.caption("About " + str(tokens) + " tokens sent")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "label": label,
            "tool_calls": trace,
            "tokens": tokens,
            "sources": sources,
        }
    )
