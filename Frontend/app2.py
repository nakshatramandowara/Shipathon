import streamlit as st
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from backend import event_recommender as er
import os

# Initialize paths
script_dir = Path(__file__).parent
EVENTS_PATH = script_dir / "events.json"

# Helper Functions
def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_mongodb():
    """Setup MongoDB connection and raise error if connection fails."""
    load_dotenv()
    MONGO_URI = os.getenv('MONGODB_URI')
    if not MONGO_URI:
        raise SystemExit("Error: MongoDB URI not found in environment variables. Exiting.")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        db = client['event_app']

        # Store collections in session state
        st.session_state.users_collection = db['users']
        st.session_state.preferences_collection = db['preferences']
        st.session_state.events_collection = db['events']
        st.session_state.mongo_setup_done = True
    except Exception as e:
        raise SystemExit(f"Error: Failed to connect to MongoDB. Details: {e}. Exiting.")

def save_user(username, password, role, department, age, year, preferences, gender, past_events):
    """Save a new user and their preferences to MongoDB."""
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
        "interests": [(len(preferences) - i) * preferences[i] for i in range(len(preferences))],
        "past_events": past_events
    }

    try:
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
    except Exception as e:
        st.error(f"MongoDB Error: {str(e)}")

def verify_user(username, password):
    """Verify if a user exists in the MongoDB collection."""
    try:
        user = st.session_state.users_collection.find_one({
            'username': username,
            'password': hash_password(password)
        })
        return user is not None
    except Exception as e:
        st.error(f"MongoDB Error: {str(e)}")
        return False

def get_user_preferences(username):
    """Fetch user preferences from MongoDB."""
    try:
        return st.session_state.preferences_collection.find_one({'name': username})
    except Exception as e:
        st.error(f"MongoDB Error: {str(e)}")
        return {}

def load_events():
    """Load events from the MongoDB collection."""
    try:
        return list(st.session_state.events_collection.find())
    except Exception as e:
        st.error(f"MongoDB Error: {str(e)}")
        return []

def display_events_as_list(events):
    """Display a list of events."""
    st.title("Event List")
    for event in events:
        st.markdown(f"### **{event.get('Title', 'Untitled Event')}**")
        date = event.get("date", "N/A")
        time = event.get("time", "N/A")
        st.markdown(f"📅 **Date:** {date}  🕒 **Time:** {time}")
        location = event.get("location", "N/A")
        st.markdown(f"📍 **Location:** {location}")
        summary = event.get("summary", "N/A")
        st.markdown(f"<p style='font-size: smaller;'>{summary}</p>", unsafe_allow_html=True)
        st.markdown("---")

def main():
    st.title("Event Recommendation System")

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None

    # Setup MongoDB
    setup_mongodb()

    # Sidebar for login/logout functionality
    with st.sidebar:
        if not st.session_state.logged_in:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login"):
                    if verify_user(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        user = st.session_state.users_collection.find_one({'username': login_username})
                        st.session_state.role = user['role']
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")
            
            with col2:
                if st.button("Register"):
                    st.session_state.register = True
        else:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.experimental_rerun()

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
        new_department = st.selectbox("Choose Department", options=departments)
        new_age = st.number_input("Enter Age", min_value=1, max_value=100, value=20, step=1, key="reg_age")
        new_year = st.number_input("Enter Degree-Year", min_value=1, max_value=10, value=2, step=1, key="reg_year")
        new_gender = st.selectbox("Choose Gender", options=gender)
        preferences = st.multiselect("Select Interests", categories)

        if st.button("Create Account"):
            save_user(new_username, new_password, role, new_department, new_age, new_year, preferences, new_gender, [])
            st.success("Account created successfully!")
            st.session_state.register = False
            st.experimental_rerun()

    # Main content - Recommendations
    if st.session_state.logged_in:
        st.subheader("Event Recommendations")
        
        with st.expander("Filters"):
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date(), datetime(2025, 12, 31).date()],
                key="date_filter"
            )
            
        filters = {
            'date_range': [d.isoformat() for d in date_range] if len(date_range) == 2 else None
        }
        
        user_prefs = get_user_preferences(st.session_state.username)
        events = load_events()
        recommended_events = er.get_user_preferences(user_prefs, events, filters)
        display_events_as_list(recommended_events)

if __name__ == "__main__":
    main()
