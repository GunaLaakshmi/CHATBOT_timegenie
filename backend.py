from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# In-memory storage for tasks (Replace with a database in production)
tasks = []

@app.route("/add-task", methods=["POST"])
def add_task():
    """Adds a new task to the schedule with a unique ID."""
    data = request.get_json()
    task_name = data.get("task")
    task_time = data.get("time")
    priority = data.get("priority")

    if not task_name or not task_time or not priority:
        return jsonify({"error": "Missing task details"}), 400

    # Generate a unique task ID
    task_id = random.randint(1000, 9999)
    
    task = {
        "id": task_id,  # Unique ID
        "task": task_name,
        "time": task_time,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    tasks.append(task)
    return jsonify({"message": "Task added successfully", "task": task})

@app.route("/schedule", methods=["GET"])
def get_schedule():
    """Returns the current schedule with task status updates."""
    current_time = datetime.now().time()

    # Update task statuses
    for task in tasks:
        task_time = datetime.strptime(task["time"], "%H:%M").time()
        if task["status"] == "pending" and current_time > task_time:
            task["status"] = "overdue"

    return jsonify({"tasks": tasks})

@app.route("/complete-task/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    """Marks a task as completed."""
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            return jsonify({"message": "Task marked as completed"})

    return jsonify({"error": "Task not found"}), 404

@app.route("/delete-task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Deletes a task based on task_id."""
    global tasks
    print(f"Received request to delete task with ID: {task_id}")  # Debugging

    task_to_delete = next((task for task in tasks if task["id"] == task_id), None)

    if task_to_delete:
        tasks = [task for task in tasks if task["id"] != task_id]
        print(f"Deleted task: {task_to_delete}")  # Debugging
        return jsonify({"message": "Task deleted successfully"})

    print(f"Task ID {task_id} not found!")  # Debugging
    return jsonify({"error": "Task not found"}), 404

@app.route("/daily-planner", methods=["POST"])
def chatbot_response():
    """Handles chatbot responses based on user messages."""
    user_message = request.json.get("message", "").lower()

    # Predefined chatbot information
    predefined_responses = {
        "what is a chatbot?": "A chatbot is an AI program that interacts with users via text or voice.",
        "how does a daily planner chatbot work?": "It schedules tasks, sets reminders, and organizes your day based on your inputs.",
        "features of a chatbot": "A chatbot can provide information, schedule tasks, answer FAQs, and interact naturally with users."
    }

    # Sample responses for task scheduling
    task_responses = [
        "I can help you schedule that! Click the 'Add to Schedule' button below to set the time and priority. ✅",
        "I'll help you plan that! Use the scheduling form below to set the details. 🗓",
        "Great idea! Click 'Add to Schedule' below to set when you'd like to do this. ⏰"
    ]

    # Sample responses for general inquiries
    general_responses = [
        "How can I assist with your daily planning?",
        "Need help organizing your day? Let me know your tasks!",
        "I'm here to help you schedule tasks and set reminders!"
    ]

    # Check if the response is predefined
    if user_message in predefined_responses:
        return jsonify({"response": predefined_responses[user_message]})

    # Generate a dynamic response
    if any(word in user_message for word in ["schedule", "remind", "plan", "set", "task", "todo"]):
        bot_response = random.choice(task_responses)
    elif "thank" in user_message:
        bot_response = "You're welcome! Let me know if you need more planning help. 😊"
    elif any(word in user_message for word in ["bye", "exit", "quit"]):
        bot_response = "Goodbye! Have a productive day. 🏆"
    else:
        bot_response = random.choice(general_responses)

    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
