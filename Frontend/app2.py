import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from pathlib import Path
import json
from backend import event_recommender as er
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Initialize paths
script_dir = Path(__file__).parent
EVENTS_PATH = script_dir / "events.json"
USER_DB_PATH = script_dir / "user_db.json"
USER_PREFS_PATH = script_dir / "user_preferences.json"

# @st.cache_data
# def start():
#     er.ensure_initialization("my_events")
def setup_mongodb():
@st.cache_resource
def setup_mongo_connection():
"""Setup MongoDB connection. Cached as a shared resource."""
MONGO_URI = os.getenv('MONGODB_URI')
if not MONGO_URI:
raise SystemExit("Error: MongoDB URI not found in environment variables.")
try:
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
client.server_info()  # Test the connection
return client
except Exception as e:
raise SystemExit(f"Error: Failed to connect to MongoDB. Details: {e}")

@st.cache_resource
def get_database_collections(_client):
"""Retrieve and cache database collections.
       Using cache_resource instead of cache_data since we're dealing with MongoDB collections."""
db = _client['event_app']
return {
'users': db['users'],
'preferences': db['preferences'],
'events': db['events']
}

# Initialize connection and retrieve collections
client = setup_mongo_connection()
collections = get_database_collections(client)

# Store collections in session state
st.session_state.users_collection = collections['users']
st.session_state.preferences_collection = collections['preferences']
st.session_state.events_collection = collections['events']
st.session_state.mongo_setup_done = True




def hash_password(password):
return hashlib.sha256(password.encode()).hexdigest()

def save_user(username, password, role, department, age, year, preferences, gender, past_events):
user_data = {
'username': username,
'password': hash_password(password),
'created_at': datetime.now().isoformat(),
'role': role
}

preferences_data = {
"name": username,
"gender": gender,
"role": role,
"age": age,
"department": department,
"year": year,
"interests": preferences,
"past_events": past_events
}

try:
# Check if the username already exists
existing_user = st.session_state.users_collection.find_one({'username': username})

if existing_user:
st.error("Username already exists. Please choose a different username.")
return  # Exit the function if username exists

# If the username does not exist, proceed with the save operation
st.session_state.users_collection.update_one(
{'username': username},
{'$set': user_data},
upsert=True
)
st.session_state.preferences_collection.update_one(
{'name': username},
{'$set': preferences_data},
upsert=True
)
st.success("Account created successfully!")
st.session_state.register = False

except Exception as e:
st.error(f"MongoDB Error: {str(e)}")


def verify_user(username, password):
try:
user = st.session_state.users_collection.find_one({
'username': username,
'password': hash_password(password)
})
return user is not None
except Exception:
return False

def get_user_preferences(username):
try:
prefs = st.session_state.preferences_collection.find_one({'name': username})
if prefs:
return prefs
except Exception:
return {}

def load_events():
with open(EVENTS_PATH, 'r') as f:
return json.load(f)

def get_recommendations(user_prefs, events, filters=None):
return er.get_user_preferences(user_prefs)

def display_events_as_list(events):
st.title("Event List")
    username = st.session_state.username
    user_data = st.session_state.preferences_collection.find_one({"name": username})
    past_events = user_data.get("past_events", []) if user_data else []

for i, event in enumerate(events):
col1, col2 = st.columns([4, 1])  # Two columns: one for the event details, one for the checkbox
        

        event_title = event.get("Title", "Untitled Event")
        is_attended = event_title in past_events  # Check if the event is in past_events

with col1:
            if event.get("attended", False):  # Dim out if attended
            if is_attended:  # Dim out if attended
st.markdown(
f"<div style='opacity: 0.5;'>"
                    f"<h3>**{event.get('Title', 'Untitled Event')}**</h3>"
                    f"<h3>**{event_title}**</h3>"
f"📅 **Date:** {event.get('date', 'N/A')}  🕒 **Time:** {event.get('time', 'N/A')}<br>"
f"📍 **Location:** {event.get('location', 'N/A')}<br>"
f"<p style='font-size: smaller;'>{event.get('summary', 'N/A')}</p>"
f"</div>",
unsafe_allow_html=True,
)
else:
                st.markdown(f"### **{event.get('Title', 'Untitled Event')}**")
                st.markdown(f"### **{event_title}**")
st.markdown(f"📅 **Date:** {event.get('date', 'N/A')}  🕒 **Time:** {event.get('time', 'N/A')}")
st.markdown(f"📍 **Location:** {event.get('location', 'N/A')}")
st.markdown(f"<p style='font-size: smaller;'>{event.get('summary', 'N/A')}</p>", unsafe_allow_html=True)
        

with col2:
            attended = st.checkbox("Attended", key=f"attended_{i}")
            if attended:
            attended = st.checkbox("Attended", key=f"attended_{i}", value=is_attended)
            if attended and not is_attended:  # If checkbox is checked and event isn't already in past_events
add_event_to_past(event)
                event["attended"] = True  # Mark the event as attended
                st.experimental_rerun()  # Refresh the page to reflect the changes
st.markdown("---")

# Function to handle the attended events
def add_event_to_past(event):
"""Add only the event title to the user's past events list in the database."""
try:
username = st.session_state.username
event_title = event.get("Title", "Untitled Event")

# Update the database to add the event title to past_events
st.session_state.preferences_collection.update_one(
{"name": username},
{"$addToSet": {"past_events": event_title}}
)
st.success(f"Event '{event_title}' marked as attended!")
except Exception as e:
st.error(f"Failed to mark event as attended: {e}")


def select_ranked_preferences(categories):

st.subheader("Rank Your Interests")
st.write("Rank the categories based on your interests. Drag the most important ones to the top.")

ranked_preferences = ["",]
none_count = 0

with st.form("ranked_preferences"):
for i, category in enumerate(categories, start=1):
selected = st.selectbox(
f"Rank {i}:",
options=["None"] + categories,
key=f"rank_{i}",
)
if selected == "None":
none_count += 1
elif selected not in ranked_preferences:
ranked_preferences.append(selected)

submitted = st.form_submit_button("Submit Rankings")

if submitted:
if len(ranked_preferences)-1 + none_count != len(categories):
st.warning("Please rank all categories uniquely, or leave them as 'None'.")

# Always return just the ranked preferences, even if incomplete
return ranked_preferences

def load_env_and_setup():
load_dotenv()
setup_mongodb()


def main():
st.title("Event Recommendation System")

load_env_and_setup()
# Initialize session state variables
if 'logged_in' not in st.session_state:
st.session_state.logged_in = False
if 'username' not in st.session_state:
st.session_state.username = None
if 'role' not in st.session_state:
st.session_state.role = None



# Sidebar for login/logout functionality
with st.sidebar:
if not st.session_state.logged_in:
st.subheader("Login")
login_username = st.text_input("Username", key="login_username")
login_password = st.text_input("Password", type="password", key="login_password")

if st.button("Login"):
if verify_user(login_username, login_password):
st.session_state.logged_in = True
st.session_state.username = login_username
user = st.session_state.users_collection.find_one({'username': login_username})
st.session_state.role = user['role']
else:
st.error("Invalid credentials")

if st.button("Register"):
st.session_state.register = True
else:
st.write(f"Welcome, {st.session_state.username}!")
if st.button("Logout"):
st.session_state.logged_in = False
st.session_state.username = None
st.session_state.role = None

# Registration form
if not st.session_state.logged_in and st.session_state.get("register", False):
st.subheader("Register New Account")
new_username = st.text_input("Choose Username", key="reg_username")
new_password = st.text_input("Choose Password", type="password", key="reg_password")

roles = ["Student", "Professor", "Organiser"]  
gender = ["Male", "Female", "Other"]
departments = ["Physics", "Maths", "Electrical", "Computer Science", "Chemical", "Mechanical", "Textile"]
categories = ["Technology", "Entertainment", "Sports", "Business", "Cultural"]

role = st.selectbox("Choose Role", options=roles)
if role == "Student":
new_department = st.selectbox("Choose Department", options=departments)
new_age = st.number_input("Enter Age", min_value=1, max_value=100, value=20, step=1, key="reg_age")
new_year = st.number_input("Enter Degree-Year", min_value=1, max_value=10, value=2, step=1, key="reg_year")
new_gender = st.selectbox("Choose Gender", options=gender)

ranked_preferences = select_ranked_preferences(categories)

if st.button("Create Account"):
save_user(
new_username, new_password, role, new_department, 
new_age, new_year, ranked_preferences, new_gender, []
)

# Main content - Recommendations
if st.session_state.logged_in:
st.subheader("Event Recommendations")

with st.expander("Filters"):
date_range = st.date_input(
"Date Range",
value=[datetime.now().date(), datetime(2025, 12, 31).date()],
key="date_filter"
)

event_types = ['All', 'Conference', 'Festival', 'Workshop', 'Competition']
selected_type = st.selectbox("Event Type", event_types)

filters = {
'date_range': [d.isoformat() for d in date_range] if len(date_range) == 2 else None,
'event_type': selected_type if selected_type != 'All' else None
}

user_prefs = get_user_preferences(st.session_state.username)
events = st.session_state.events_collection.find()
recommended_events = get_recommendations(user_prefs, list(events), filters)
display_events_as_list(recommended_events)

if __name__ == "__main__":
main()
