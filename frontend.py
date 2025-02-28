import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API Backend URL
API_URL = "http://127.0.0.1:5000"  

# Title Section with Styling
st.markdown("""
    <style>
    .title-container {
        background: linear-gradient(-45deg, #FF6B6B, #4ECDC4, #FFD93D, #6C63FF);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .title-text {
        color: white;
        font-size: 3em;
        font-weight: bold;
    }
    
    .subtitle-text {
        color: white;
        font-size: 1.4em;
        margin-top: 10px;
    }
    </style>
    <div class="title-container">
        <div class="title-text">✨ Task Genie</div>
        <div class="subtitle-text">Your Intelligent Daily Planning Assistant</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar Information
st.sidebar.title("📜 Task History")
st.sidebar.info("""
**Task Genie** is your personal assistant for organizing daily activities. 
With **Task Genie**, you can:
- 📝 Schedule tasks with priority levels
- ⏰ Set reminders for important activities
- ✅ Track and complete tasks efficiently
""")

# Fetch Scheduled Tasks
try:
    history_response = requests.get(f"{API_URL}/schedule")
    if history_response.status_code == 200:
        schedule_data = history_response.json()
        tasks = schedule_data.get("tasks", [])

        if tasks:
            selected_task = st.sidebar.radio(
                "📝 Scheduled Tasks", 
                [f"{task['task']} - {task['time']} ({task['priority']})" for task in tasks]
            )
except requests.exceptions.ConnectionError:
    st.sidebar.error("📡 Connection failed. Check server status.")

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Chat & Plan", "📊 Schedule Overview", "📖 Help & Guide"])

# Chat & Planning
with tab1:
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": "👋 Hello! I'm **Task Genie**, your Daily Planner Assistant. "
                       "I can help you schedule tasks, set reminders, and organize your day. "
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("💬 Ask me about your schedule...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        response = requests.post(f"{API_URL}/daily-planner", json={"message": user_input}).json()
        bot_response = response["response"]
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()

    # "Add to Task" Button
    st.markdown("### ✏️ Add a New Task")
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name", placeholder="e.g., Morning Exercise")
        task_time = st.time_input("Select Time")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submit_button = st.form_submit_button("➕ Add to Task")

        if submit_button and task_name:
            formatted_time = task_time.strftime("%H:%M")  # Convert time to HH:MM format
            task_data = {
                "task": task_name,
                "time": formatted_time,
                "priority": priority
            }
            response = requests.post(f"{API_URL}/add-task", json=task_data)
            if response.status_code == 200:
                st.success(f"✅ Task '{task_name}' added successfully!")
            else:
                st.error("❌ Failed to add task. Please try again.")

# Schedule Overview
with tab2:
    st.markdown("## 📊 Schedule Overview")
    try:
        schedule_response = requests.get(f"{API_URL}/schedule")
        if schedule_response.status_code == 200:
            schedule_data = schedule_response.json()
            tasks = schedule_data.get("tasks", [])
            
            if tasks:
                df = pd.DataFrame(tasks)
                st.dataframe(df[['task', 'time', 'priority']])
                
                for task in tasks:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{task['task']}** - {task['time']} ({task['priority']})")
                    with col2:
                        if st.button("🗑️ Delete", key=task['id']):
                            delete_response = requests.delete(f"{API_URL}/delete-task/{task['id']}")

                            if delete_response.status_code == 200:
                                st.success(f"✅ Task '{task['task']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete task. Try again.")
            else:
                st.info("🌟 Your schedule is clear! Ask me to help you create tasks.")
    except requests.exceptions.ConnectionError:
        st.error("📡 Connection failed. Please check server status.")

# Help & Guide
with tab3:
    st.markdown("""
    ## 📖 How to Use Task Genie

    Task Genie helps you stay organized and manage your day effectively. Here’s how you can use it:

    ### 1️⃣ Chat & Plan 🗣️
    - Type a request like **"Remind me to take medicine at 9 PM"** in the chat.
    - Task Genie will confirm and schedule it for you.
    - Ask about your schedule by typing **"What are my tasks for today?"**

    ### 2️⃣ Add a Task 📝
    - Click **'Add a New Task'** and enter:
      - Task Name
      - Task Time
      - Priority Level (Low, Medium, High)
    - Click **"➕ Add to Task"** to save it.

    ### 3️⃣ View & Manage Tasks ✅
    - Go to the **'Schedule Overview'** tab to see your tasks.
    - Click **🗑️ Delete** to remove a completed task.
    - Refresh your schedule anytime to see updates.

    🚀 Stay on track with Task Genie!
    """)
