import csv
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

import agents

load_dotenv()


def get_api_key():
    try:
        return st.secrets["MISTRAL_API_KEY"]
    except Exception:
        return os.getenv("MISTRAL_API_KEY")


st.set_page_config(page_title="Support Dashboard", page_icon="S", layout="centered")

st.title("Support Dashboard")
st.caption("Cinema and bank support chat. Powered by Mistral.")

# ---------------- sidebar ----------------

with st.sidebar:
    st.header("Support controls")

    model = st.selectbox("Model", agents.AVAILABLE_MODELS, index=0)

    st.subheader("Booking context")
    booking_context = st.text_area(
        "Paste a booking confirmation to attach to the next question",
        value=st.session_state.get("booking_context", ""),
        height=100,
    )
    st.session_state.booking_context = booking_context

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Chat history lives in this browser session and resets on refresh.")


# ---------------- secrets ----------------

api_key = get_api_key()
if not api_key:
    st.error("MISTRAL_API_KEY is missing. Add it to Day27/.env or Streamlit secrets.")
    st.stop()


# ---------------- session state ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None


def _streamlit_confirm(prompt):
    st.session_state.pending_confirmation = {
        "prompt": prompt,
        "action": getattr(agents, "_pending_action", None),
    }
    return False


agents.confirm_action = _streamlit_confirm


def save_feedback(question, answer, label, feedback):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback.csv")
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["timestamp", "question", "answer", "label", "feedback"])
        writer.writerow([datetime.now().isoformat(), question, answer, label, feedback])


def _last_user_question(index):
    for i in range(index - 1, -1, -1):
        if st.session_state.messages[i]["role"] == "user":
            return st.session_state.messages[i]["content"]
    return ""


# ---------------- render history ----------------

for index, message in enumerate(st.session_state.messages):
    role = message["role"]
    with st.chat_message(role):
        st.write(message["content"])

        if role == "assistant":
            label = message.get("label")
            tool_calls = message.get("tool_calls") or []

            with st.expander("Routed label and tool calls", expanded=False):
                st.write(f"Routed to: **{label or 'unknown'}**")
                if tool_calls:
                    for call in tool_calls:
                        st.write(f"- `{call['name']}` {call.get('args', {})}")
                        st.write(f"  => {call.get('result', '')}")
                else:
                    st.write("No tool calls.")

            feedback = message.get("feedback")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Thumbs up", key=f"up_{index}"):
                    save_feedback(
                        _last_user_question(index),
                        message["content"],
                        label,
                        "up",
                    )
                    st.session_state.messages[index]["feedback"] = "up"
                    st.rerun()
            with col2:
                if st.button("Thumbs down", key=f"down_{index}"):
                    save_feedback(
                        _last_user_question(index),
                        message["content"],
                        label,
                        "down",
                    )
                    st.session_state.messages[index]["feedback"] = "down"
                    st.rerun()

            if feedback:
                st.caption(f"Feedback recorded: {feedback}")


# ---------------- pending confirmation ----------------

pending = st.session_state.get("pending_confirmation")
if pending and pending.get("action"):
    action = pending["action"]
    st.warning(pending.get("prompt", "Confirmation required."))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm", key="confirm_pending"):
            if action.get("type") == "block_card":
                result = agents.block_card(action.get("card_id"), confirmed=True)
            elif action.get("type") == "transfer_money":
                result = agents.transfer_money(
                    action.get("from_account"),
                    action.get("to_account"),
                    action.get("amount"),
                    confirmed=True,
                )
            else:
                result = "Unknown pending action."

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result,
                    "label": action.get("type", "general"),
                    "tool_calls": [],
                    "feedback": None,
                }
            )
            st.session_state.pending_confirmation = None
            st.rerun()
    with col2:
        if st.button("Cancel", key="cancel_pending"):
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "Action cancelled.",
                    "label": "general",
                    "tool_calls": [],
                    "feedback": None,
                }
            )
            st.session_state.pending_confirmation = None
            st.rerun()


# ---------------- handle new input ----------------

prompt = st.chat_input("Type a customer question...")

if prompt:
    st.session_state.pending_confirmation = None
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "label": None, "tool_calls": [], "feedback": None}
    )

    # Build the query sent to the agents, attaching booking context if provided.
    context = st.session_state.get("booking_context", "").strip()
    agent_query = prompt
    if context:
        agent_query = "Booking context:\n" + context + "\n\nQuestion: " + prompt

    label = agents.route(agent_query, model=model)
    if label is None:
        label = "general"

    info = agents.SPECIALISTS.get(label, agents.SPECIALISTS["general"])
    trace = []
    answer = info["runner"](
        info["system_prompt"],
        agent_query,
        info["tools"],
        model=model,
        trace=trace,
    )

    if answer is None:
        answer = "Sorry, I'm having trouble connecting right now. Please try again in a moment."

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "label": label,
            "tool_calls": trace,
            "feedback": None,
        }
    )

    st.rerun()
