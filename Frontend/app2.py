
import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from pathlib import Path
from pymongo import MongoClient
from backend import event_recommender as er
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGO_URI)
db = client['event_app']
users_collection = db['users']
preferences_collection = db['preferences']
events_collection = db['events']

@st.cache_data
def start():
    er.ensure_initialization("my_events")
    
    # Uncomment this section if you need to initialize events from a file
    # documents = load_initial_events()
    # for idx, doc in enumerate(documents):
    #     doc["id"] = idx
    #     events_collection.update_one(
    #         {"id": idx},
    #         {"$set": doc},
    #         upsert=True
    #     )

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(username, password, role, department, age, year, preferences, gender, past_events):
    # Save user authentication data
    user_data = {
        'username': username,
        'password': hash_password(password),
        'created_at': datetime.now(),
        'role': role
    }
    users_collection.update_one(
        {'username': username},
        {'$set': user_data},
        upsert=True
    )
    
    # Save user preferences
    preferences_data = {
        "name": username,
        "gender": gender,
        "role": role,
        "age": age,
        "department": department,
        "year": year,
        "interests": [(len(preferences)-i)*preferences[i] for i in range(len(preferences))],
        "past_events": past_events
    }
    preferences_collection.update_one(
        {'name': username},
        {'$set': preferences_data},
        upsert=True
    )

def verify_user(username, password):
    user = users_collection.find_one({
        'username': username,
        'password': hash_password(password)
    })
    return user is not None

def get_user_preferences(username):
    prefs = preferences_collection.find_one({'name': username})
    return prefs if prefs else {}


# Function to save a new event


# Function to delete an event



def load_events():
    with open(EVENTS_PATH, 'r') as f:
        return json.load(f)

# Recommendation system
def get_recommendations(user_prefs, events, filters=None):
    print(user_prefs)
    return er.get_user_preferences(user_prefs)

def display_events_as_list(events):
    """
    Displays a list of events in Streamlit with a formatted layout.
    """
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
# Ranked interest selection
def select_ranked_preferences(categories):
    st.subheader("Rank Your Interests")
    st.write("Rank the categories based on your interests. Drag the most important ones to the top. You can leave some ranks as 'None' if not interested in those categories.")

    ranked_preferences = []
    none_count = 0
    with st.form("ranked_preferences"):
        for i, category in enumerate(categories, start=1):
            selected = st.selectbox(
                f"Rank {i}:",
                options=["None"] + categories,
                key=f"rank_{i}",
            )
            # Allow multiple "None" and ignore it for rankings
            if selected == "None":
                none_count += 1
            elif selected not in ranked_preferences:
                ranked_preferences.append(selected)

        submitted = st.form_submit_button("Submit Rankings")
        if submitted:
            if len(ranked_preferences) + none_count != len(categories):
                st.warning("Please rank all categories uniquely, or leave them as 'None'.")
            else:
                return ranked_preferences  # Only return valid preferences
    return None




# Main app
def main():
    st.title("Event Recommendation System")
    init_storage()

    # Login/Register sidebar
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
                        with open(USER_DB_PATH, 'r+') as f:
                            users = json.load(f)
                            st.session_state.role = users[login_username]['role']
                        st.rerun()
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
                st.rerun()

    # # Registration form
    # if not st.session_state.logged_in and st.session_state.get('register', False):
    #     st.subheader("Register New Account")
    #     new_username = st.text_input("Choose Username", key="reg_username")
    #     new_password = st.text_input("Choose Password", type="password", key="reg_password")
        
    #     roles = ['Student', "Professor","Organiser"]  
    #     categories = ['Technology', 'Entertainment', 'Sports', 'Business', 'Cultural']
    #     gender = ["Male", "Female","Other"]
    #     departments = ["Physics", "Maths", "Electrical","Computer Science","Chemical","Mechanical","Textile"]

    #     role = st.selectbox("Choose Role", options=roles)
    #     if role == 'Student':
    #         new_department = st.selectbox("Choose department", options=departments)
    #         new_age = st.number_input("Enter Age", min_value=1, max_value=100, value=20, step=1,key="reg_age")
    #         new_year = st.number_input("Enter your degree-year",min_value=1, max_value=10, value=2, step=1, key="reg_year")
    #         new_gender = st.selectbox("choose gender", options=gender)

    #         st.subheader("Preferences")
    #         selected_categories = st.multiselect(
    #             "Select your interests",
    #             options=categories
    #         )
        
    #     if st.button("Create Account"):
    #         preferences = {
    #             'interested_categories': selected_categories
    #         }
    #         save_user(new_username, new_password, role, new_department, new_age, new_year, preferences["interested_categories"], new_gender, [])
    #         st.success("Account created successfully!")
    #         st.session_state.register = False
    #         st.rerun()
    # Updated registration form to include ranked preferences
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
    
            # Use the new ranked preferences function
        
        ranked_preferences = select_ranked_preferences(categories)
    
        if st.button("Create Account"):
            preferences = ranked_preferences if ranked_preferences else [""]
            save_user(
                new_username, new_password, role, new_department, 
                new_age, new_year, preferences, new_gender, []
            )
            st.success("Account created successfully!")
            st.session_state.register = False
            st.rerun()

    # Main content - Recommendations
    if st.session_state.logged_in:
        st.subheader("Event Recommendations")
        
        # Filters
        with st.expander("Filters"):
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date(), datetime(2025, 12, 31).date()],
                key="date_filter"
            )
            
            event_types = ['All', 'Conference', 'Festival', 'Workshop','Competition']
            selected_type = st.selectbox("Event Type", event_types)
            
        # Apply filters
        filters = {
            'date_range': [d.isoformat() for d in date_range] if len(date_range) == 2 else None,
            'event_type': selected_type if selected_type != 'All' else None
        }
        
        # Get and display recommendations
        user_prefs = get_user_preferences(st.session_state.username)
        events = load_events()
        recommended_events = get_recommendations(user_prefs, events, filters)
        display_events_as_list(recommended_events)

if __name__ == "__main__":
    main()
