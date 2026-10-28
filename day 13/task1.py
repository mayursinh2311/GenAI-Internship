import chromadb
import hashlib
import math

# Create ChromaDB client
client = chromadb.Client()

# Create collection
collection = client.create_collection(
    name="doc_genai"
)

# Documents
documents = [
    "Python is a programming language",
    "Java is used for software development",
    "Machine learning is part of AI",
    "ChromaDB stores vector data",
    "Artificial intelligence is growing"
]

# Simple custom embedding function
def make_embeddings(texts):
    result = []

    for text in texts:
        vector = [0.0] * 128

        for word in text.lower().split():
            index = int(
                hashlib.sha256(word.encode()).hexdigest()[:8],
                16
            ) % 128

            vector[index] += 1.0

        magnitude = math.sqrt(sum(x * x for x in vector))

        if magnitude:
            vector = [x / magnitude for x in vector]

        result.append(vector)

    return result


# Add documents with custom embeddings
collection.add(
    ids=["1", "2", "3", "4", "5"],
    documents=documents,
    embeddings=make_embeddings(documents)
)

# Search
query = "Python programming"

result = collection.query(
    query_embeddings=make_embeddings([query]),
    n_results=2
)

print(result)