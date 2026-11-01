from mistralai.client import Mistral
from pypdf import PdfReader
from dotenv import load_dotenv
import streamlit as st
import chromadb
import os
load_dotenv()

client_mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+chunk_size])
        start += chunk_size - overlap
    return chunks

st.title("Documents")

files = st.file_uploader("upload your pdf here", type="pdf", accept_multiple_files=True)

if files and st.button("Process"):
    chroma = chromadb.Client()
    collection = chroma.get_or_create_collection("multiple_pdf")

    metadatas = []
    documents = []
    ids = []
    chunk_id = 0
    for k in files:
        reader = PdfReader(k)
        text = "".join(page.extract_text() for page in reader.pages)
        for chunk in chunk_text(text):
            documents.append(chunk)
            metadatas.append({"source":k.name})
            ids.append(str(chunk_id))
            chunk_id += 1
    
    collection.add(
        metadatas = metadatas,
        documents = documents,
        ids = ids
    )

    st.session_state.collection = collection
    st.success(f"Indexed {len(documents)} chunks from {len(files)} files")

question = st.text_input("Ask a Question :")
if question and "collection" in st.session_state:
    results = st.session_state.collection.query(
        query_texts=[question],
        n_results=4
    ) 
    chunks = results["documents"][0]
    sources = results["metadatas"][0]

    context = "\n\n".join(chunks)
    prompt = f"""give answer only using this pdf otherwise, say "your answer not in pdf"
    Context :{context}
    
    Question : {question}
    """
    with st.spinner("wait ..."):
        response = client_mistral.chat.complete(
            model = "mistral-small-latest",
            temperature = 0.2,
            messages = [
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )
    
    st.write(response.choices[0].message.content)

    st.caption("Sources : " + ", ".join(set(s["source"] for s in sources)))