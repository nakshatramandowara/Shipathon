
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import hashlib
from pathlib import Path
from backend import event_recommender as er

script_dir = Path(__file__).parent
EVENTS_PATH = script_dir/"events.json"


def start():
    er.initialize_collection("my_events")

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
    try:
        documents = json.load(f)
        print(documents)
    except json.JSONDecodeError as e:
        print("JSON decoding failed:", e)



    for idx, doc in enumerate(documents):
        doc["id"] = idx  
        result = er.add_event_to_database(doc)

start()

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# File paths
USER_DB_PATH = script_dir/"user_db.json"
USER_PREFS_PATH = script_dir/"user_preferences.json"

# Initialize storage files if they don't exist


def create_upload_page():
    """Create the event upload page."""
    st.title("Upload New Event")
    
    with st.form("event_upload_form"):
        st.subheader("Event Details")
        
        # Basic Information
        title = st.text_input("Event Title*", help="Enter the name of the event")
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input(
                "Event Date*",
                min_value=datetime.now().date(),
                help="Select the event date or application deadline"
            )
        with col2:
            event_time = st.time_input(
                "Event Time*",
                value=None,
                help="Select the event start time"
            )
        
        # Event Type and Target Audience
        col3, col4 = st.columns(2)
        with col3:
            types = ['recruitment', 'cultural','technical']
            event_type = st.selectbox(
                "Type*",
                options=types,
                help="Select whether this is an event or recruitment posting"
            )
        with col4:
            target_audience = st.text_input("Target_Audience*")
        
        # Location
        location = st.text_input(
            "Location*",
            help="Enter the event location or specify if it's virtual"
        )
        
        # Description
        description = st.text_area(
            "Description*",
            help="Provide a detailed description of the event",
            height=150
        )
        
        # Additional Details based on event type
        if event_type == 'Recruitment':
            company = st.text_input("Company Name*")
            position = st.text_input("Position*")
            requirements = st.text_area("Requirements*", height=100)
        
        submitted = st.form_submit_button("Upload Event")
        
        if submitted:
            # Validate required fields
            required_fields = {
                'title': title,
                'date': date,
                'time': event_time,
                'location': location,
                'description': description,
                'target_audience': target_audience
            }
            
            if event_type == 'Recruitment':
                required_fields.update({
                    'company': company,
                    'position': position,
                    'requirements': requirements
                })
            
            # Check if any required field is empty
            missing_fields = [field for field, value in required_fields.items() 
                            if not value]
            
            if missing_fields:
                st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                # Create event data dictionary
                event_data = {
                    'title': title,
                    'date': date.isoformat(),
                    'time': event_time.strftime('%H:%M'),
                    'type': event_type,
                    'location': location,
                    'description': description,
                    'target_audience': target_audience,
                }
                
                # Add recruitment-specific fields if applicable
                if event_type == 'Recruitment':
                    event_data.update({
                        'company': company,
                        'position': position,
                        'requirements': requirements
                    })
                
                # Save the event
                try:
                    er.add_event_to_database(event_data)
                    st.success("Event uploaded successfully!")
                    # Clear form (by forcing a rerun)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving event: {str(e)}")

def init_storage():
    if not USER_DB_PATH.exists():
        with open(USER_DB_PATH, 'w') as f:
            json.dump({}, f)
    
    if not USER_PREFS_PATH.exists():
        with open(USER_PREFS_PATH, 'w') as f:
            json.dump({}, f)
    
    if not EVENTS_PATH.exists():
        sample_events = {}
        with open(EVENTS_PATH, 'w') as f:
            json.dump(sample_events, f)

# User authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

    save_user(new_username, new_password, role, new_department, new_age, new_year, preferences,gender,[])

def save_user(username, password, role, department, age,year,preferences,gender,past_events):
    with open(USER_DB_PATH, 'r+') as f:
        users = json.load(f)
        users[username] = {
            'password': hash_password(password),
            'created_at': datetime.now().isoformat(),
            'role':role
        }
        f.seek(0)
        json.dump(users, f)
    
    with open(USER_PREFS_PATH, 'r+') as f:
        prefs = json.load(f)
        prefs[username] = {"name":username,"gender":gender,"role":role,"age":age,"department":department,"year":year,"interests":preferences,"past_events":past_events}
        f.seek(0)
        json.dump(prefs, f)

def verify_user(username, password):
    with open(USER_DB_PATH, 'r') as f:
        users = json.load(f)
        if username in users and users[username]['password'] == hash_password(password):
            return True
    return False

def get_user_preferences(username):
    with open(USER_PREFS_PATH, 'r') as f:
        prefs = json.load(f)
        return prefs.get(username, {})

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

    Args:
        events (list): List of dictionaries, each representing an event.
    """
    st.title("Event List")
    
    for event in events:
        # Title in bold
        st.markdown(f"### **{event.get('Title', 'Untitled Event')}**")
        
        # Date and time with icons
        date = event.get("date", "N/A")
        time = event.get("time", "N/A")
        st.markdown(f"📅 **Date:** {date}  🕒 **Time:** {time}")
        
        # Location
        location = event.get("location", "N/A")
        st.markdown(f"📍 **Location:** {location}")
        
        # Summary in smaller font
        summary = event.get("summary", "N/A")
        st.markdown(f"<p style='font-size: smaller;'>{summary}</p>", unsafe_allow_html=True)
        
        # Divider for better readability
        st.markdown("---")  # Horizontal line



# Main app
def main():
    st.session_state.current_page = "main"
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
                st.session_state.current_page = 'main'
                st.rerun()

    # Registration form
    if not st.session_state.logged_in and st.session_state.get('register', False):
        st.subheader("Register New Account")
        new_username = st.text_input("Choose Username", key="reg_username")
        new_password = st.text_input("Choose Password", type="password", key="reg_password")
        
        roles = ['Organiser','Student','professor']
        categories = ['Technology', 'Entertainment', 'Sports', 'Business', 'Arts']
        gender = ["male","female"]
        departments = ["physics","maths","electrical"]


        role = st.selectbox("Choose Role", options = roles)
        if(role == 'Student'):
            new_department = st.selectbox("Choose department",options = departments)
            new_age = st.number_input("Enter Age",key = "reg_age")
            new_year = st.number_input("Enter your degree-year",key = "reg_year")
            new_gender = st.selectbox("choose gender",options = gender)


            st.subheader("Preferences")
            
            selected_categories = st.multiselect(
                "Select your interests",
                options=categories
            )
        
        if st.button("Create Account"):
            preferences = {
                'interested_categories': selected_categories
            }
            save_user(new_username, new_password, role, new_department, new_age, new_year, preferences["interested_categories"],new_gender,[])
            st.success("Account created successfully!")
            st.session_state.register = False
            st.rerun()

    # Main content - Recommendations
    if st.session_state.logged_in and st.session_state.role=='Student':
        st.subheader("Event Recommendations")
        
        # Filters
        with st.expander("Filters"):
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date(), datetime(2025, 12, 31).date()],
                key="date_filter"
            )
            
            event_types = ['All', 'Conference', 'Festival', 'Workshop']
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
        
    with st.sidebar:
        if st.session_state.logged_in and st.session_state.role == 'Organiser':
            st.write(f"Welcome, {st.session_state.username}!")
            
            # Show upload button only for admin
            if st.button("Upload New Event"):
                st.session_state.current_page = 'upload'
            if st.button("View Events"):
                st.session_state.current_page = 'main'
            
        else:
            # [Previous login code remains the same...]
            pass

    # Page routing
    if st.session_state.current_page == 'upload' :
        create_upload_page()
        
    else:
        # [Previous main page code remains the same...]
        pass


if __name__ == "__main__":
    main()
