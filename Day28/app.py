"""Streamlit UI for the Hotel Guest Assistant (Day 28).

The app keeps chat memory in st.session_state, moderates each message, routes it
to a specialist, and streams the answer. All agent logic lives in agents.py.
"""

import os

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
st.caption("Room service, reservations, facilities and hotel info. Powered by Mistral.")

if agents.client is None:
    st.error("MISTRAL_API_KEY is missing. Add it to Day28/.env and reload.")
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


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:
    st.header("Guest controls")

    model = st.selectbox("Model", agents.AVAILABLE_MODELS, index=0)

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
    st.write("Try asking:")
    st.caption("Show me the food menu.")
    st.caption("Is a deluxe room free on 2026-12-25?")
    st.caption("Book a standard room for Asha on 2026-12-25.")
    st.caption("What time does the spa open on Saturday?")
    st.caption("What is the Wi-Fi password?")

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

            if message.get("tokens"):
                st.caption("About " + str(message["tokens"]) + " tokens sent")


# --------------------------------
# NEW INPUT
# --------------------------------

prompt = st.chat_input("Ask about room service, reservations, facilities or hotel info...")

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
            }
        )
        st.stop()

    # 2. Router with fallback to general.
    label = agents.route(prompt, model=model)
    if label is None:
        label = "general"

    info = agents.SPECIALISTS.get(label, agents.SPECIALISTS["general"])

    # 3. Token estimate for the request that is about to go out.
    history = st.session_state.messages[-agents.MAX_CONTEXT_MESSAGES:]
    request_messages = agents.build_messages(info["system_prompt"], prompt, history)
    tokens = agents.estimate_messages_tokens(request_messages)

    st.session_state.last_request_tokens = tokens
    st.session_state.total_tokens += tokens

    # 4. Run the specialist and stream the answer.
    trace = []
    with st.chat_message("assistant"):
        answer = st.write_stream(
            agents.run_specialist_stream(
                info["system_prompt"],
                prompt,
                info["tools"],
                model=model,
                trace=trace,
                history=history,
            )
        )

    if not answer:
        answer = "Sorry, I am having trouble connecting right now. Please try again in a moment."

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "label": label,
            "tool_calls": trace,
            "tokens": tokens,
        }
    )
