import json
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

st.set_page_config(page_title="Study Buddy", page_icon="📚")
st.title("Study Buddy")
st.write("Chat with your textbook or research paper, take a quiz, or get a summary.")

# get the api key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("MISTRAL_API_KEY is not set. Add it to Day15/task3/.env")
    st.stop()

# create the mistral client
mistral = Mistral(api_key=api_key)

# open the local database
db_path = os.path.join(folder, "chroma_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection("study_docs")


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


def get_all_text():
    # get every chunk so the quiz and summary can use the whole document
    data = collection.get()
    documents = data["documents"]
    metadatas = data["metadatas"]

    if documents is None or len(documents) == 0:
        return ""

    total = 0
    for doc in documents:
        total = total + len(doc)

    # for a very long document, take every nth chunk
    step = 1
    if total > 12000:
        step = total // 12000 + 1

    text = ""
    i = 0
    while i < len(documents):
        page = metadatas[i].get("page")
        text = text + "[" + metadatas[i]["source"] + ", page " + str(page) + "]\n"
        text = text + documents[i] + "\n\n"
        i = i + step

    return text[:12000]


def ask_question(question):
    # find the chunks that are closest to the question
    if collection.count() == 0:
        return "Upload a document first.", False, "", None, ""

    results = collection.query(query_texts=[question], n_results=4)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # build the context text
    context = ""
    for i in range(len(documents)):
        page = metadatas[i].get("page")
        context = context + "[" + metadatas[i]["source"] + ", page " + str(page) + "]\n"
        context = context + documents[i] + "\n\n"

    prompt = "Answer the student's question using only the document context below. "
    prompt = prompt + "If the answer is not in the context, reply exactly: I couldn't find that in the document. "
    prompt = prompt + "Do not add a source line.\n\n"
    prompt = prompt + "Document context:\n" + context
    prompt = prompt + "Student question: " + question

    response = mistral.chat.complete(
        model="mistral-small-latest",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content
    if answer is None:
        answer = ""

    if answer.lower().startswith("i couldn't find"):
        return "I couldn't find that in the document.", False, "", None, ""

    source = metadatas[0]["source"]
    page = metadatas[0].get("page")
    text = documents[0]
    return answer, True, source, page, text


def make_quiz(difficulty):
    context = get_all_text()
    if context == "":
        return None

    prompt = "Create exactly 5 quiz questions at " + difficulty + " difficulty from the document below. "
    prompt = prompt + "Return JSON like this: {\"questions\": [{\"question\": \"...\", \"answer\": \"...\"}]}. "
    prompt = prompt + "Use only the document.\n\nDocument:\n" + context

    response = mistral.chat.complete(
        model="mistral-small-latest",
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content
    if raw is None:
        return None

    try:
        data = json.loads(raw)
    except Exception:
        return None

    questions = data.get("questions", [])
    if len(questions) > 5:
        questions = questions[:5]
    return questions


def make_summary():
    context = get_all_text()
    if context == "":
        return None

    prompt = "Summarize the document below in 5 to 8 short bullet points. "
    prompt = prompt + "Start each bullet with '- '. Use only the document. "
    prompt = prompt + "Do not add an introduction or conclusion.\n\nDocument:\n" + context

    response = mistral.chat.complete(
        model="mistral-small-latest",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# sidebar
with st.sidebar:
    st.header("Study document")
    files = st.file_uploader("Upload a PDF", type="pdf", accept_multiple_files=True)

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
        st.info("No document yet. Upload a PDF to start.")
    else:
        st.write("Files:")
        for source in sources:
            st.write("- " + source)

    if st.button("Reset database"):
        try:
            client.delete_collection("study_docs")
        except Exception:
            pass
        collection = client.get_or_create_collection("study_docs")
        st.session_state.messages = []
        st.session_state.quiz = None
        st.session_state.summary = None
        st.rerun()


# keep the chat and results in memory
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "summary" not in st.session_state:
    st.session_state.summary = None


tab1, tab2, tab3 = st.tabs(["Ask", "Quiz", "Summarize"])


with tab1:
    st.subheader("Ask the document")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and message["found"]:
                st.caption("Source: " + message["source"] + ", page " + str(message["page"]))
                with st.expander("Source text"):
                    st.write(message["text"])

    question = st.chat_input("Ask about the chapter...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Looking through the document..."):
            answer, found, source, page, text = ask_question(question)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "found": found,
            "source": source,
            "page": page,
            "text": text,
        })
        st.rerun()


with tab2:
    st.subheader("Quiz yourself")
    st.write("Generate 5 questions from the uploaded document.")

    difficulty = st.radio("Difficulty", ["easy", "medium", "hard"], index=1, horizontal=True)

    if st.button("Generate 5 quiz questions"):
        if collection.count() == 0:
            st.warning("Upload a document first.")
        else:
            with st.spinner("Writing quiz questions..."):
                quiz = make_quiz(difficulty)
            if quiz is None:
                st.error("Could not create the quiz. Please try again.")
            else:
                st.session_state.quiz = quiz

    if st.session_state.quiz is not None:
        for i in range(len(st.session_state.quiz)):
            item = st.session_state.quiz[i]
            st.write("**Q" + str(i + 1) + ". " + item["question"] + "**")
            with st.expander("Show answer"):
                st.write(item["answer"])


with tab3:
    st.subheader("Summarize the document")
    st.write("Get a short bullet summary of the uploaded document.")

    if st.button("Summarize this document"):
        if collection.count() == 0:
            st.warning("Upload a document first.")
        else:
            with st.spinner("Writing summary..."):
                summary = make_summary()
            if summary is None:
                st.error("Could not create the summary. Please try again.")
            else:
                st.session_state.summary = summary

    if st.session_state.summary is not None:
        st.write(st.session_state.summary)