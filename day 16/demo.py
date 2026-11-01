import chromadb

client = chromadb.PersistentClient(path="./vectordb")

collection = client.get_or_create_collection("space_exploration")

collection.add(
    documents = ["The Mars Rover Perseverance landed on Mars in 2021 to search for signs of ancient life.", "The International Space Station orbits Earth at about 400 km altitude."],
    metadatas = [{"sources": "nasa.pdf"}, {"sources": "esa.pdf"}],
    ids = ["space1", "space2"]
)

result = collection.query(
    query_texts = ["Tell me about the Mars rover mission"],
    n_results = 1
)

print(result)