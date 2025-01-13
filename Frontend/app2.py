import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from pathlib import Path
import json
from backend import event_recommender as er
import os
from dotenv import load_dotenv

# Initialize paths
script_dir = Path(__file__).parent
EVENTS_PATH = script_dir / "events.json"
USER_DB_PATH = script_dir / "user_db.json"
USER_PREFS_PATH = script_dir / "user_preferences.json"

# @st.cache_data
# def start():
#     er.ensure_initialization("my_events")

# @st.cache_data
def setup_mongodb():
    """Setup MongoDB connection."""
    from pymongo import MongoClient
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

def main():
    st.title("Event Recommendation System")
    load_dotenv()
    
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
                st.success("Account created successfully!")
                st.session_state.register = False

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
