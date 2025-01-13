# EventConnect: Personalized Campus Activity Hub

## Team Aries - Shipathon Project  
- **Team Members**:  
  - Aditi Herur  
  - Kahaan Parikh  
  - Nakshtra Mandowara  
  - Harshul Anand  
  - Shubham Sahu   

---

## Problem Statement  
Develop a comprehensive and user-friendly digital platform tailored to enhance student engagement and participation in campus events at IIT Delhi. The platform should serve as a personalized gateway for students to seamlessly discover, explore, and interact with a diverse array of events, including departmental seminars, cultural and technical club activities, and flagship festivals such as Rendezvous and Tryst.  

The solution incorporates advanced features such as intelligent event recommendations based on individual preferences, academic and extracurricular interests, and personal schedules, fostering accessibility and personalization to enrich the overall campus experience.  

---

## Methodology  

### 1. **Data Collection**  
- Collected event data from IIT Delhi’s clubs, departments, and cultural organizations (e.g., Rendezvous, Tryst).  
- Sources included official emails and Instagram posts shared by event organizers.  
- Ensured up-to-date and accurate details for event recommendations and discovery.  

### 2. **Data Processing and Categorization**  
- Extracted emails in `.eml` format and stored them in a Google Drive folder.  
- Used Python libraries (`email`, `glob`) to process `.eml` files directly from the Drive.  
- Implemented Retrieval-Augmented Generation (RAG) using the **Gemini API**.  
  - Generated detailed event descriptions, summaries, and historical insights for accurate representation.  

### 3. **Personalization**  
- Users provide inputs like preferred timings, interests, and club/event preferences.  
- Filters enable users to customize event discovery (e.g., by interest: cultural, technical, or sports).  
- Created a tailored event discovery experience based on user inputs.  

### 4. **Platform Development**  
- Built the platform using **Streamlit**, enabling real-time event discovery and display.  
- Features include input forms for user preferences and event suggestions based on availability and interests.  

---

## Tools Used  
### 1. **MongoDB (Database Management)**

-Integrated MongoDB to handle structured and semi-structured event data effectively.

-Provided scalability for storing user profiles, preferences, and interaction history.

-Enabled fast querying and aggregation for analytics and personalized recommendations.

-Offered a robust backup and recovery system to ensure data reliability.

### 2. **Gemini LLM API**  
- Automated structured event detail extraction from email content.  
- Parsed key details (event date, time, location, audience, summaries) and generated unique event IDs.  

### 3. **Vector Database (Qdrant)**  
- Stored and managed event embeddings for efficient similarity searches.  
- Enabled personalized event recommendations by analyzing user preferences and past interactions.  

### 4. **Front-End Development (Streamlit Community Share)**  
- Created an intuitive and interactive user interface.  
- Allowed dynamic input forms, real-time event data display, and backend integration.






---

## Future Advancements  
- Expand data collection using advanced tools to include websites, Instagram, and other sources.  
- Integrate Instagram Display API for real-time event data updates and enhanced recommendations.  
- Broaden event coverage to improve personalization and user experience.  

---

## How to Use the Platform  
1. Clone this repository:  
   ```bash
   git clone https://github.com/<your-repo-name>.git
