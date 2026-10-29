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

st.set_page_config(page_title="Company Knowledge Assistant", page_icon="📄", layout="wide")
st.title("Company Knowledge Assistant")
st.write("Ask about HR policy, leave, or benefits. Answers come only from the uploaded PDFs.")

# get the api key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("MISTRAL_API_KEY is not set. Add it to Day15/task1/.env")
    st.stop()

# create the mistral client
mistral = Mistral(api_key=api_key)

# open the local database
db_path = os.path.join(folder, "chroma_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection("hr_policies")


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


def make_source_text(chunks):
    # build a line like "Retrieved from: hr_policies.pdf (pages 1, 2, 3)"
    sources = []
    for chunk in chunks:
        if chunk["source"] not in sources:
            sources.append(chunk["source"])

    parts = []
    for source in sources:
        pages = []
        for chunk in chunks:
            if chunk["source"] == source and chunk["page"] not in pages:
                pages.append(chunk["page"])
        pages.sort()

        if len(pages) == 1:
            parts.append(source + " (page " + str(pages[0]) + ")")
        else:
            page_text = ""
            for page in pages:
                if page_text != "":
                    page_text = page_text + ", "
                page_text = page_text + str(page)
            parts.append(source + " (pages " + page_text + ")")

    return "Retrieved from: " + ", ".join(parts)


def ask_question(question):
    # find the chunks that are closest to the question
    if collection.count() == 0:
        return "I don't know. No policy documents are indexed yet.", False, None, [], ""

    results = collection.query(query_texts=[question], n_results=5)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # build the context text and the chunk list
    context = ""
    chunks = []
    for i in range(len(documents)):
        source = metadatas[i]["source"]
        page = metadatas[i].get("page")
        context = context + "[" + source + ", page " + str(page) + "]\n"
        context = context + documents[i] + "\n\n"
        chunks.append({
            "text": documents[i],
            "source": source,
            "page": page,
            "distance": distances[i],
        })

    prompt = "You are an HR policy assistant. Answer the employee's question using only the context below. "
    prompt = prompt + "If the answer is not in the context, reply exactly: I don't know. "
    prompt = prompt + "Do not add a source line. Do not use outside knowledge and do not guess.\n\n"
    prompt = prompt + "Context:\n" + context
    prompt = prompt + "Question: " + question

    response = mistral.chat.complete(
        model="mistral-small-latest",
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content
    if answer is None:
        answer = ""

    if answer.lower().startswith("i don't know"):
        return "I don't know.", False, distances[0], chunks, ""

    return answer, True, distances[0], chunks, make_source_text(chunks)


# sidebar
with st.sidebar:
    st.header("Policy documents")
    files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

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
        st.info("No documents yet. Upload a PDF to start.")
    else:
        st.write("Files:")
        for source in sources:
            st.write("- " + source)

    if st.button("Reset database"):
        try:
            client.delete_collection("hr_policies")
        except Exception:
            pass
        collection = client.get_or_create_collection("hr_policies")
        st.session_state.messages = []
        st.rerun()


# keep the chat in memory
if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and message["found"]:
            st.caption(message["source_text"])
            st.caption("Best distance: " + str(round(message["distance"], 4)) + " (lower is closer)")
            with st.expander("Retrieved chunks"):
                for chunk in message["chunks"]:
                    st.write("**" + chunk["source"] + "** (page " + str(chunk["page"]) + ", distance " + str(round(chunk["distance"], 4)) + ")")
                    st.write(chunk["text"])


question = st.chat_input("Ask about company policy...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("Searching policies..."):
        answer, found, distance, chunks, source_text = ask_question(question)
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "found": found,
        "distance": distance,
        "chunks": chunks,
        "source_text": source_text,
    })
    st.rerun()