# !pip install -U sentence-transformers
# !pip install -U qdrant-client

from pathlib import Path
script_dir = Path(__file__).parent

from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import json

# Global variables
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(":memory:")
SIMILARITY_THRESHOLD = 0.835
_is_initialized = False

def ensure_initialization():
    """
    Ensures the collection is initialized and populated with events.
    Uses a global flag to prevent multiple initializations.
    """
    global _is_initialized
    
    if not _is_initialized:
        # Initialize collection
        initialize_collection("my_events")
        
        # Load and add events
        events_file = script_dir/"events.json"
        try:
            with open(events_file, 'r') as f:
                documents = json.load(f)
            
            for idx, doc in enumerate(documents):
                doc["id"] = idx
                add_event_to_database(doc)
            
            _is_initialized = True
        except FileNotFoundError:
            raise Exception("Events file not found. Please ensure events.json exists in the correct directory.")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in events.json")

def initialize_collection(collection_name):
    """
    Initializes a Qdrant collection if it does not already exist.
    """
    collections = client.get_collections().collections
    existing_collections = [col.name for col in collections]
    
    if collection_name not in existing_collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )

def is_similar_event(client, collection_name, new_vector, threshold=SIMILARITY_THRESHOLD):
    search_results = client.search(
        collection_name=collection_name,
        query_vector=new_vector,
        limit=1,
    )
    if len(search_results) > 0:
        print(f"Similarity score: {search_results[0].score}")
    return len(search_results) > 0 and search_results[0].score > threshold

def add_event_to_database(doc, collection_name="my_events", threshold=SIMILARITY_THRESHOLD):
    values_string = f"{doc['Title']} {doc['location']} {doc['summary']} {doc['target_audience']}"
    event_vector = encoder.encode(values_string).tolist()

    if is_similar_event(client, collection_name, event_vector, threshold):
        return f"Skipped event: {doc['Title']} (similar to an existing event)."

    client.upload_points(
        collection_name=collection_name,
        points=[models.PointStruct(id=doc.get("id", 0), vector=event_vector, payload=doc)],
    )
    return f"Inserted event: {doc['Title']} into the database."

def get_user_preferences(user_data,
    name_weight = 0,
    gender_weight = 1,
    role_weight = 3,
    department_weight = 2,
    year_weight = 1,
    interests_weight = 5,
    past_events_weight = 1,
    NA_weight = 2,
):
    """
    Get recommendations for a user based on their preferences.
    Ensures collection is initialized before searching.
    """
    # Ensure collection is initialized before searching
    ensure_initialization()
    
    weighted_text = (
        f"{(user_data['name'] + ' ') * int(name_weight)}" +
        f"{(user_data['gender'] + ' ') * int(gender_weight)}" +
        f"{(user_data['role'] + ' ') * int(role_weight)}" +
        f"{(user_data['department'] + ' ') * int(department_weight)}" +
        f"{(str(user_data['year']) + ' ') * int(year_weight)}" +
        f"{(' '.join(user_data['interests']) + ' ') * int(interests_weight)}"  +
        f"{(' '.join(user_data['past_events']) + ' ') * int(past_events_weight)}"
    )
    
    na_vector = encoder.encode("N/A").tolist()
    weighted_vector = encoder.encode(weighted_text).tolist()
    combined_vector = [p - NA_weight*n for p, n in zip(weighted_vector, na_vector)]

    # Query the vector database
    hits = client.query_points(
        collection_name="my_events",
        query=combined_vector,
        limit=10
    ).points

    # Collect the resulting payloads
    resulting_data = []
    for hi in hits:
        resulting_data.append(hi.payload)

    # Save results
    output_file = script_dir/"search_results.json"
    with open(output_file, "w") as f:
        json.dump(resulting_data, f, indent=4)

    return resulting_data

def main():
    """
    Main function for testing the recommender system.
    """
    ensure_initialization()
    
    user_data_file = script_dir/"user_data.json"
    try:
        with open(user_data_file, 'r') as f:
            user_data = json.load(f)
        results = get_user_preferences(user_data)
        print(f"Found {len(results)} recommendations")
    except FileNotFoundError:
        print("User data file not found")
    except json.JSONDecodeError:
        print("Invalid JSON format in user data file")

if __name__ == '__main__':
    main()
