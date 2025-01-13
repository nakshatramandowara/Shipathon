from pathlib import Path
script_dir = Path(__file__).parent

from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import json

# Global variables
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(":memory:")
_is_initialized = False

def ensure_initialization(name="my_events"):
    """
    Ensures the collection is initialized and populated with events.
    Uses a global flag to prevent multiple initializations.
    """
    global _is_initialized
    
    if True:
        # Initialize collection
        collections = client.get_collections().collections
        if name not in [col.name for col in collections]:
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=encoder.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE,
                ),
            )
        
        # Load and add events
        events_file = script_dir/"events.json"
    
        with open(events_file, 'r') as f:
            print(f)
            documents = json.load(f)
        
        # Create points list for batch upload
        points = []
        tags_weight = 4.0
        for idx, doc in enumerate(documents):
            values_string = f"{doc['Title']} {doc['location']} {doc['summary']} {doc['target_audience']}"
            vector = encoder.encode(values_string).tolist()
            tags_vector = encoder.encode(' '.join(doc["Tags"])).tolist()
            vector = [(a + b*tags_weight) for a,b in zip(vector, tags_vector)]
            
            
            points.append(models.PointStruct(
                id=idx,
                vector=vector,
                payload=doc
            ))
        
        # Batch upload all points
        client.upload_points(
            collection_name=name,
            points=points
        )
        
        _is_initialized = True
        print(f"Initialized with {len(points)} events")
            
       
def get_user_preferences(user_data,
    name_weight=0.0,
    gender_weight=0.3,
    role_weight=3.0,
    department_weight=2.0,
    year_weight=0.5,
    interests_weight=5.5,
    past_events_weight=2.0,
    NA_weight=0.8,
    delete=False,
):
    """
    Get recommendations for a user based on their preferences.
    Ensures collection is initialized before searching.
    """
    # Ensure collection is initialized before searching
    if(delete):
        collections = client.get_collections().collections
        name="my_events"
        if name in [col.name for col in collections]:
            client.delete_collection(name)
    ensure_initialization()
    
    # Initialize the combined vector with zeros
    combined_vector = [0.0] * len(encoder.encode("dummy").tolist())  # Dummy encoding for vector size
    
    # Helper function to scale vectors by weight and add to combined vector
    def add_weighted_vector(text, weight):
        if not text or weight == 0:
            return
        vector = encoder.encode(text).tolist()
        for i in range(len(combined_vector)):
            combined_vector[i] += vector[i] * weight
    
    # Add weighted vectors for each user attribute
    add_weighted_vector(user_data.get('name', ''), name_weight)
    add_weighted_vector(user_data.get('gender', ''), gender_weight)
    add_weighted_vector(user_data.get('role', ''), role_weight)
    add_weighted_vector(user_data.get('department', ''), department_weight)
    add_weighted_vector(str(user_data.get('year', '')), year_weight)
    add_weighted_vector(' '.join(user_data.get('interests', [])), interests_weight)
    add_weighted_vector(' '.join(user_data.get('past_events', [])), past_events_weight)
    
    # Subtract weighted "N/A" vector
    na_vector = encoder.encode("N/A").tolist()
    for i in range(len(combined_vector)):
        combined_vector[i] -= NA_weight * na_vector[i]

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

# def main():
#     """
#     Main function for testing the recommender system.
#     """
#     ensure_initialization()
    
#     user_data_file = script_dir/"user_data.json"
#     try:
#         with open(user_data_file, 'r') as f:
#             user_data = json.load(f)
#         results = get_user_preferences(user_data)
#         print(f"Found {len(results)} recommendations")
#     except FileNotFoundError:
#         print("User data file not found")
#     except json.JSONDecodeError:
#         print("Invalid JSON format in user data file")

if __name__ == '__main__':
    main()
