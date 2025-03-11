import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API Backend URL
API_URL = "http://127.0.0.1:5000"

import streamlit as st

st.markdown("""
    <style>
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .title-container {
        background: linear-gradient(-45deg, #FF6B6B, #4ECDC4, #FFD93D, #6C63FF);
        background-size: 400% 400%;
        animation: gradient 10s ease infinite;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
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
    .floating-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #6C63FF;
        color: white;
        font-size: 1.4em;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        cursor: pointer;
        transition: transform 0.3s ease-in-out;
    }
    .floating-button:hover {
        transform: scale(1.1);
        background: #4ECDC4;
    }
    </style>
    <div class="title-container">
        <div class="title-text">✨ Task Genie</div>
        <div class="subtitle-text">Your Intelligent Daily Planning Assistant</div>
    </div>
    <button class="floating-button" onclick="alert('Add a new task!')">➕</button>
""", unsafe_allow_html=True)



# Load knowledge.csv
@st.cache_data
def load_knowledge():
    try:
        df = pd.read_csv(r"C:\Users\guna laakshmi\Downloads\chatbot\knowledge.csv", encoding="ISO-8859-1")
        knowledge_dict = dict(zip(df['question'].str.lower(), df['answer']))
        return knowledge_dict
    except Exception as e:
        st.error(f"⚠️ Error loading knowledge base: {e}")
        return {}

knowledge_base = load_knowledge()

# Initialize chat history in session state (without duplicating messages)
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "👋 Hello! Ask me anything about scheduling tasks or general knowledge!"
    }]

# 🔹 Sidebar Information
st.sidebar.title("📜 Task History")
st.sidebar.info("""
**Task Genie** helps you:
- 📝 Schedule tasks efficiently
- ⏰ Set reminders for key activities
- ✅ Track and manage tasks with ease
""")

# Fetch Tasks & Reminders
try:
    history_response = requests.get(f"{API_URL}/schedule")
    reminders_response = requests.get(f"{API_URL}/reminders")

    # 🎯 Display Scheduled & Completed Tasks
    if history_response.status_code == 200:
        tasks = history_response.json().get("tasks", [])

        if tasks:
            # Categorize tasks
            today = datetime.today().date()
            pending_tasks = [task for task in tasks if task["status"] == "pending"]
            completed_tasks = [task for task in tasks if task["status"] == "completed"]
            overdue_tasks = [task for task in pending_tasks if datetime.strptime(task["date"], "%Y-%m-%d").date() < today]

            # 🔴 Overdue Tasks (Highlighted)
            if overdue_tasks:
                st.sidebar.markdown("### 🔴 Overdue Tasks")
                for idx, task in enumerate(overdue_tasks):
                    st.sidebar.write(f"⏳ **{task['task']}** - {task['date']} ({task['priority']})")

            # 🟡 Scheduled Tasks
            if pending_tasks:
                st.sidebar.markdown("### 🟡 Scheduled Tasks")
                for idx, task in enumerate(pending_tasks):
                    st.sidebar.write(f"📌 {task['task']} - {task['date']} ({task['priority']})")

                    # Ensure unique keys using index + task ID
                    col1, col2 = st.sidebar.columns([1, 1])
                    with col1:
                        if st.button("✅ Done", key=f"complete_{task['id']}_{idx}"):
                            requests.post(f"{API_URL}/complete-task/{task['id']}")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{task['id']}_{idx}"):
                            requests.delete(f"{API_URL}/delete-task/{task['id']}")
                            st.rerun()

            # ✅ Completed Tasks
            if completed_tasks:
                st.sidebar.markdown("### ✅ Completed Tasks")
                for idx, task in enumerate(completed_tasks):
                    st.sidebar.write(f"✔️ {task['task']} - {task['date']}")

        else:
            st.sidebar.info("No tasks found. Add new tasks using Task Genie! ✅")

    else:
        st.sidebar.error("⚠️ Unable to load scheduled tasks.")

    # 🔔 Display Reminders
    st.sidebar.markdown("### 🔔 Active Reminders")
    if reminders_response.status_code == 200:
        reminders = reminders_response.json().get("reminders", [])

        if reminders:
            for idx, reminder in enumerate(reminders):
                st.sidebar.write(f"⏰ **{reminder['task']}** - {reminder['time']} ({reminder['priority']})")
        else:
            st.sidebar.info("No active reminders.")

    else:
        st.sidebar.error("⚠️ Unable to load reminders.")

except requests.exceptions.ConnectionError:
    st.sidebar.error("📡 Connection failed. Check the API server status.")
    
    # 🔹 Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Chat & Plan", "📊 Schedule Overview", "📖 Help & Guide"])

# 📌 Chat & Planning
with tab1:
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("💬 Ask me about your schedule...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 🔹 Check if question exists in knowledge base
        lower_input = user_input.lower()
        if lower_input in knowledge_base:
            bot_response = knowledge_base[lower_input]
        else:
            try:
                response = requests.post(f"{API_URL}/daily-planner", json={"message": user_input})
                response.raise_for_status()
                response_data = response.json()
                bot_response = response_data.get("response", "I'm not sure how to respond.")

                # 🔹 Extract entity information
                extracted_info = response_data.get("entities", "")
                if extracted_info and extracted_info != "No specific details detected.":
                    bot_response += f"\n\n🔍 **Extracted Details:**\n{extracted_info}"

                # If a scheduling-related response is detected, show the "Add Task" button
                if "Do you want to schedule something specific?" in bot_response:
                    st.session_state["show_task_form"] = True

                # Automatically open the task form if a date/time is detected
                if extracted_info and extracted_info != "No specific details detected.":
                    st.session_state["show_task_form"] = True
                    # Extract the detected date/time
                    if "📅 **Date:**" in extracted_info:
                        detected_date = extracted_info.split("📅 **Date:**")[1].split("\n")[0].strip()
                        st.session_state["extracted_date"] = detected_date
                    if "⏰ **Time:**" in extracted_info:
                        detected_time = extracted_info.split("⏰ **Time:**")[1].split("\n")[0].strip()
                        st.session_state["extracted_time"] = detected_time

            except requests.exceptions.RequestException as e:
                bot_response = f"❌ API request failed: {e}"

        # Append bot response and rerun
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()

    # Show "➕ Add Task" button when scheduling is suggested
    if "show_task_form" in st.session_state:
        if st.button("➕ Add Task"):
            del st.session_state["show_task_form"]

    # 🔹 Add a Task
    st.markdown("## ✏️ Add a New Task")
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name", placeholder="e.g., Morning Exercise")
        task_date = st.date_input("Select Date", 
            value=datetime.strptime(st.session_state.get("extracted_date", datetime.today().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
        )
        task_time = st.time_input("Select Time",
            value=datetime.strptime(st.session_state.get("extracted_time", "08:00"), "%H:%M").time()
        )
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        reminder = st.checkbox("🔔 Set Reminder")
        submit_button = st.form_submit_button("➕ Add to Task")

        if submit_button and task_name:
            task_data = {
                "task": task_name,
                "date": task_date.strftime("%Y-%m-%d"),
                "time": task_time.strftime("%H:%M"),
                "priority": priority,
                "reminder": reminder
            }

            try:
                response = requests.post(f"{API_URL}/add-task", json=task_data)
                if response.status_code == 200:
                    st.success(f"✅ Task '{task_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add task.")
            except requests.exceptions.RequestException:
                st.error("❌ Could not connect to the server.")
# 📌 Schedule Overview
with tab2:
    st.markdown("## 📊 Schedule Overview")

    try:
        schedule_response = requests.get(f"{API_URL}/schedule")
        if schedule_response.status_code == 200:
            tasks = schedule_response.json().get("tasks", [])
            
            if tasks:
                df = pd.DataFrame(tasks)
                st.dataframe(df[['task', 'date', 'time', 'priority', 'status']])

                for task in tasks:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.write(f"📅 {task['date']} - **{task['task']}** - 🕒 {task['time']} ({task['priority']})")

                    with col2:
                        if task["status"] == "pending":
                            if st.button("✅ Complete", key=f"complete_{task['id']}"):
                                complete_response = requests.post(f"{API_URL}/complete-task/{task['id']}")
                                if complete_response.status_code == 200:
                                    st.success("🎉 Task marked as completed!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update status.")

                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{task['id']}"):
                            delete_response = requests.delete(f"{API_URL}/delete-task/{task['id']}")
                            if delete_response.status_code == 200:
                                st.success("✅ Task deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete task.")

                    with col4:
                        if st.button("✏️ Edit", key=f"edit_{task['id']}"):
                            st.session_state["edit_task_id"] = task["id"]
                            st.session_state["edit_task_name"] = task["task"]
                            st.session_state["edit_task_date"] = task["date"]
                            st.session_state["edit_task_time"] = task["time"]
                            st.session_state["edit_task_priority"] = task["priority"]

                # Check if a task is selected for editing
                if "edit_task_id" in st.session_state:
                    st.markdown("## 📝 Edit Task")

                    with st.form("edit_task_form", clear_on_submit=False):
                        new_task_name = st.text_input("Task Name", st.session_state["edit_task_name"])
                        new_task_date = st.date_input("Select Date", datetime.strptime(st.session_state["edit_task_date"], "%Y-%m-%d").date())
                        new_task_time = st.time_input("Select Time", datetime.strptime(st.session_state["edit_task_time"], "%H:%M").time())
                        new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], 
                                                    index=["Low", "Medium", "High"].index(st.session_state["edit_task_priority"]))

                        update_button = st.form_submit_button("💾 Update Task")

                        if update_button:
                            updated_task = {
                                "task": new_task_name,
                                "date": new_task_date.strftime("%Y-%m-%d"),
                                "time": new_task_time.strftime("%H:%M"),
                                "priority": new_priority
                            }

                            update_response = requests.put(f"{API_URL}/update-task/{st.session_state['edit_task_id']}", json=updated_task)

                            if update_response.status_code == 200:
                                st.success("✅ Task updated successfully!")
                                del st.session_state["edit_task_id"]  # Remove edit state
                                st.rerun()
                            else:
                                st.error("❌ Failed to update task.")

    except requests.exceptions.ConnectionError:
        st.error("📡 Connection failed.")

# 📌 Help & Guide
with tab3:
    st.markdown("""
📖 How to Use Task Genie
Task Genie is your intelligent daily planning assistant, helping you manage tasks efficiently through an interactive chatbot.

🎯 Chat & Plan 🗣️

1. Type messages like "Schedule a meeting tomorrow at 3 PM" to create tasks.
2. Ask "Show my schedule for the week" to get an overview.
3. Get personalized responses based on extracted details like dates, times, and priorities.

📝 Add a Task Manually

1. Enter the task name, date, time, and priority in the input form.
2. Choose 🔔 Set Reminder if needed.
3. Click ➕ Add to Task to save it.

📊 Manage Your Tasks

1. View all scheduled tasks in Schedule Overview.
2. ✅ Mark tasks as completed when done.
3.🗑️ Delete tasks that are no longer needed.
    """)
