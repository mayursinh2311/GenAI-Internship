import random
from pymilvus import MilvusClient

# Create Milvus Lite database
client = MilvusClient("college_demo.db")

collection_name = "college_information"

# Start fresh on every run
if client.has_collection(collection_name=collection_name):
    client.drop_collection(collection_name=collection_name)

# Create collection
client.create_collection(
    collection_name=collection_name,
    dimension=768,
)

# College information
docs = [
    "ADMISSION: Students can apply for admission after completing their 12th standard.",
    "FEES: Students must pay their semester fees before the last payment date.",
    "EXAMINATION: Students must carry their college identity card during examinations.",
    "LIBRARY: Students can borrow up to 3 books for 15 days.",
    "ATTENDANCE: Students must maintain at least 75 percent attendance.",
    "SPORTS: The college organizes annual sports competitions for students.",
]

# Generate random vectors
vectors = [
    [random.uniform(-1, 1) for _ in range(768)]
    for _ in docs
]

# Prepare data
data = [
    {
        "id": i,
        "vector": vectors[i],
        "text": docs[i]
    }
    for i in range(len(docs))
]

# Insert data
client.insert(
    collection_name=collection_name,
    data=data
)

# Search query
query = "What is the minimum attendance required?"

query_vectors = [
    [random.uniform(-1, 1) for _ in range(768)]
]

# Search records
res = client.search(
    collection_name=collection_name,
    data=query_vectors,
    limit=3,
    output_fields=["text"],
)

# Display result
print("College Information:")
print(res)

# Delete collection
client.drop_collection(
    collection_name=collection_name
)

print("Collection deleted successfully!")