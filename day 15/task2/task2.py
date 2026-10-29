import os

import chromadb
import streamlit as st
from dotenv import load_dotenv
from mistralai.client import Mistral
from pypdf import PdfReader

# find the folder that this file is in
folder = os.path.dirname(os.path.abspath(__file__))

# read the .env file
load_dotenv(os.path.join(folder, ".env"))

st.set_page_config(page_title="SkyHawk Pro Support", page_icon="🚁", layout="wide")
st.title("SkyHawk Pro Support")
st.write("Ask about setup, flying, camera, or troubleshooting. Answers come only from the manual.")

# get the api key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("MISTRAL_API_KEY is not set. Add it to Day15/task2/.env")
    st.stop()

# create the mistral client
mistral = Mistral(api_key=api_key)

# open the local database
db_path = os.path.join(folder, "chroma_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection("support_docs")


def read_pdf(file):
    # read every page and keep the page number
    reader = PdfReader(file)
    pages = []
    for i in range(len(reader.pages)):
        text = reader.pages[i].extract_text()
        if text is None:
            text = ""
        pages.append((i + 1, text))
    return pages


def split_text(text, size=800, overlap=100):
    # join the lines, then cut the text into small chunks
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + size].strip()
        if chunk != "":
            chunks.append(chunk)
        start = start + size - overlap
    return chunks


def add_pdf(file):
    # skip a file that is already in the database
    old = collection.get(where={"source": file.name})
    if len(old["ids"]) > 0:
        return 0

    pages = read_pdf(file)
    ids = []
    documents = []
    metadatas = []

    for page_number, page_text in pages:
        page_chunks = split_text(page_text)
        for i in range(len(page_chunks)):
            ids.append(file.name + "::p" + str(page_number) + "::" + str(i))
            documents.append(page_chunks[i])
            metadatas.append({"source": file.name, "page": page_number})

    if len(documents) == 0:
        return 0

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)


def make_suggestions(question, answer):
    # ask mistral for 3 short follow-up questions
    prompt = "Suggest 3 short follow-up questions a customer might ask next. "
    prompt = prompt + "Return exactly 3 questions separated by the | character. "
    prompt = prompt + "Do not add numbering or extra text.\n\n"
    prompt = prompt + "Customer question: " + question + "\n"
    prompt = prompt + "Answer given: " + answer

    try:
        response = mistral.chat.complete(
            model="mistral-small-latest",
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content
    except Exception:
        return []

    if text is None:
        return []

    suggestions = []
    parts = text.split("|")
    for part in parts:
        part = part.strip()
        if part != "":
            if not part.endswith("?"):
                part = part + "?"
            suggestions.append(part)

    return suggestions[:3]


def ask_question(question):
    # find the chunks that are closest to the question
    if collection.count() == 0:
        return "I couldn't find that. Please contact support@company.com", False, "", None, "", []

    results = collection.query(query_texts=[question], n_results=4)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # build the context text
    context = ""
    for i in range(len(documents)):
        page = metadatas[i].get("page")
        context = context + "[" + metadatas[i]["source"] + ", page " + str(page) + "]\n"
        context = context + documents[i] + "\n\n"

    prompt = "You are a customer support assistant. Answer the customer's question using only the manual context below. "
    prompt = prompt + "If the answer is not in the context, reply exactly: I don't know. "
    prompt = prompt + "Do not add a source line. Keep the answer clear and short.\n\n"
    prompt = prompt + "Manual context:\n" + context
    prompt = prompt + "Customer question: " + question

    response = mistral.chat.complete(
        model="mistral-small-latest",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content
    if answer is None:
        answer = ""

    if answer.lower().startswith("i don't know"):
        return "I couldn't find that. Please contact support@company.com", False, "", None, "", []

    source = metadatas[0]["source"]
    page = metadatas[0].get("page")
    text = documents[0]
    suggestions = make_suggestions(question, answer)
    return answer, True, source, page, text, suggestions


# sidebar
with st.sidebar:
    st.header("Product manual")
    files = st.file_uploader("Upload the manual PDF", type="pdf", accept_multiple_files=True)

    if files is not None:
        for file in files:
            added = add_pdf(file)
            if added > 0:
                st.success("Added " + str(added) + " chunks from " + file.name)

    data = collection.get()
    st.write("Chunks in database:", len(data["ids"]))

    sources = []
    if data["metadatas"] is not None:
        for meta in data["metadatas"]:
            if meta["source"] not in sources:
                sources.append(meta["source"])

    if len(sources) == 0:
        st.info("No manual yet. Upload a PDF to start.")
    else:
        st.write("Files:")
        for source in sources:
            st.write("- " + source)

    if st.button("Reset database"):
        try:
            client.delete_collection("support_docs")
        except Exception:
            pass
        collection = client.get_or_create_collection("support_docs")
        st.session_state.messages = []
        st.rerun()


# keep the chat in memory
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


last_index = len(st.session_state.messages) - 1

for i in range(len(st.session_state.messages)):
    message = st.session_state.messages[i]

    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant":
            if message.get("found", True):
                st.caption("Source: " + message["source"] + ", page " + str(message["page"]))
                with st.expander("Source section"):
                    st.write(message["text"])

            if message.get("feedback") is not None:
                st.caption("Thanks for your feedback.")
            else:
                col1, col2 = st.columns(2)
                if col1.button("👍 Helpful", key="up_" + str(i)):
                    message["feedback"] = "up"
                    st.rerun()
                if col2.button("👎 Not helpful", key="down_" + str(i)):
                    message["feedback"] = "down"
                    st.rerun()

            if i == last_index and len(message.get("suggestions", [])) > 0:
                st.write("**You might also ask:**")
                for j in range(len(message["suggestions"])):
                    if st.button(message["suggestions"][j], key="sug_" + str(i) + "_" + str(j)):
                        st.session_state.pending_question = message["suggestions"][j]
                        st.rerun()


question = st.chat_input("Ask about your SkyHawk Pro...")

if st.session_state.pending_question is not None:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("Searching the manual..."):
        answer, found, source, page, text, suggestions = ask_question(question)
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "found": found,
        "source": source,
        "page": page,
        "text": text,
        "suggestions": suggestions,
        "feedback": None,
    })
    st.rerun()