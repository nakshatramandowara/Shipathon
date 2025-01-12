
# !pip install -U sentence-transformers
# !pip install -U qdrant-client

from pathlib import Path
script_dir = Path(__file__).parent

# from IPython.display import Markdown, display

from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("all-MiniLM-L6-v2")

import json
from qdrant_client import QdrantClient, models

# Define similarity threshold
SIMILARITY_THRESHOLD = 0.835

# Initialize Qdrant client
client = QdrantClient(":memory:")

# Function to initialize the Qdrant collection
def initialize_collection(collection_name):
    """
    Initializes a Qdrant collection if it does not already exist.
    Args:
        client: Qdrant client instance.
        collection_name: Name of the collection to initialize.
        encoder: Encoder used for determining vector size.
    """
    collections = client.get_collections().collections
    existing_collections = [col.name for col in collections]
    
    if collection_name in existing_collections:
        # print(f"Collection {collection_name} already exists.")
        pass
    else:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )
        print(f"Collection {collection_name} created.")


# Function to check for similar events
def is_similar_event(client, collection_name, new_vector, threshold=SIMILARITY_THRESHOLD):
    search_results = client.search(
        collection_name=collection_name,
        query_vector=new_vector,
        limit=1,
    )
    if len(search_results) > 0:
        print(f"Similarity score: {search_results[0].score}")
    return len(search_results) > 0 and search_results[0].score > threshold

# Function to add a single event to the database
def add_event_to_database(doc, collection_name="my_events", threshold=SIMILARITY_THRESHOLD):
    """
    Add a single event to the Qdrant database, ensuring no duplicates based on similarity.
    Args:
        client: Qdrant client instance.
        encoder: Encoder used for vectorizing text.
        doc: Dictionary containing event details.
        collection_name: Name of the Qdrant collection.
        threshold: Similarity threshold to avoid duplicate entries.
    Returns:
        str: Status message indicating the result.
    """
    values_string = f"{doc['Title']} {doc['location']} {doc['summary']} {doc['target_audience']}"
    event_vector = encoder.encode(values_string).tolist()

    if is_similar_event(client, collection_name, event_vector, threshold):
        return f"Skipped event: {doc['Title']} (similar to an existing event)."

    client.upload_points(
        collection_name=collection_name,
        points=[models.PointStruct(id=doc.get("id", 0), vector=event_vector, payload=doc)],
    )
    return f"Inserted event: {doc['Title']} into the database."

# from google.colab import drive
# drive.mount('/content/drive')

# def to_markdown(text):
#   text=text.replace('•', '  *')
#   return Markdown(textwrap.indent(text,'> ',predicate=lambda _: True))

def get_user_preferences(user_data,
  name_weight = 0,
  gender_weight = 1,
  role_weight = 3,
  department_weight = 2,
  year_weight = 1,
  interests_weight = 5,
  past_events_weight = 1,
  NA_weight = 0.6,
):
  '''
  dumps results in search_results.json
  '''
  weighted_text = (
      f"{(user_data['name'] + ' ') * int(name_weight)}" +
      f"{(user_data['gender'] + ' ') * int(gender_weight)}" +
      f"{(user_data['role'] + ' ') * int(role_weight)}" +
      f"{(user_data['department'] + ' ') * int(department_weight)}" +
      f"{(str(user_data['year']) + 'st year' + ' ') * int(year_weight)}" +
      f"{(' '.join(user_data['interests']) + ' ') * int(interests_weight)}"  +
      f"{(' '.join(user_data['past_events']) + ' ') * int(past_events_weight)}"
  )
  na_vector=encoder.encode("N/A").tolist()
  weighted_vector=encoder.encode(weighted_text).tolist()

  combined_vector = [p - NA_weight*n for p, n in zip(weighted_vector , na_vector)]
  print("searching \n", weighted_text)

  # Query the vector database
  hits = client.query_points(
      collection_name="my_events",
      query=combined_vector,
      limit=10
  ).points

  # Collect the resulting payloads as dictionaries
  resulting_data = []
  for hi in hits:
      hit = hi.payload
      print(hi.score)

      # Skip hits below a certain score threshold (optional)
    #   if hi.score < 0.1:  # Variable parameter, tweak as needed
    #       continue

      resulting_data.append(hit)

  # Save the resulting data as a JSON file
  output_file = script_dir/r'search_results.json'
  with open(output_file, "w") as f:
      json.dump(resulting_data, f, indent=4)

  return resulting_data

def main():
  # Load events from JSON file
  events_file = script_dir/r'events.json'
  print(events_file)
  with open(events_file, 'r') as f:
      documents = json.load(f)

  # Initialize the Qdrant collection
  initialize_collection("my_events")

  # Add events to the database
  for idx, doc in enumerate(documents):
      doc["id"] = idx  # Assign a unique ID
      result = add_event_to_database(doc)
      print(result)
  user_data_file = script_dir/r'user_data.json'
  with open(user_data_file, 'r') as f:
    user_data = json.load(f)
  get_user_preferences(user_data)

if __name__ == '__main__':
  main()