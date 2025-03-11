from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import pandas as pd
import spacy
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# In-memory storage for tasks
tasks = []

# Function to extract entities (Date, Time, Person) using spaCy
def extract_entities(text):
    doc = nlp(text)
    date_entity = None
    time_entity = None
    person_entities = []

    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_entity = ent.text
        elif ent.label_ == "TIME":
            time_entity = ent.text
        elif ent.label_ == "PERSON":
            person_entities.append(ent.text)

    return {
        "DATE": date_entity,
        "TIME": time_entity,
        "PERSON": person_entities if person_entities else None
    }

# Function to interact with Gemini AI
def talk_with_gemini(user_input):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(user_input)

        if hasattr(response, "text") and response.text:
            return response.text.strip()
        else:
            return "Sorry, I couldn't process that. Try rephrasing!"
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"

# Route to add a new task
@app.route("/add-task", methods=["POST"])
def add_task():
    data = request.json
    try:
        task = {
            "id": len(tasks) + 1,
            "task": data["task"],
            "date": data.get("date", "Not specified"),
            "time": data["time"],
            "priority": data["priority"],
            "reminder": data.get("reminder", False),
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        tasks.append(task)
        return jsonify({"message": "Task added successfully", "task": task}), 200
    except KeyError:
        return jsonify({"error": "Invalid task data"}), 400

# Route to get scheduled tasks
@app.route("/schedule", methods=["GET"])
def get_schedule():
    return jsonify({"tasks": tasks})

# Route to get reminders
@app.route("/reminders", methods=["GET"])
def get_reminders():
    reminders = [task for task in tasks if task.get("reminder", False)]
    return jsonify({"reminders": reminders})

# Route to mark a task as completed
@app.route("/complete-task/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            return jsonify({"message": "Task marked as completed"})
    return jsonify({"error": "Task not found"}), 404

# Route to delete a task
@app.route("/delete-task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    global tasks
    task_to_delete = next((task for task in tasks if task["id"] == task_id), None)
    if task_to_delete:
        tasks.remove(task_to_delete)
        return jsonify({"message": f"Task '{task_to_delete['task']}' deleted successfully"})
    return jsonify({"error": "Task not found"}), 404

# Route to update a task
@app.route("/update-task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.json
    for task in tasks:
        if task["id"] == task_id:
            task["task"] = data.get("task", task["task"])
            task["date"] = data.get("date", task["date"])
            task["time"] = data.get("time", task["time"])
            task["priority"] = data.get("priority", task["priority"])
            task["reminder"] = data.get("reminder", task["reminder"])
            return jsonify({"message": "Task updated successfully!", "task": task}), 200
    return jsonify({"error": "Task not found!"}), 404

# Route for chatbot conversation
@app.route("/daily-planner", methods=["POST"])
def chatbot_response():
    user_message = request.json.get("message", "").lower()
    detected_entities = extract_entities(user_message)

    if "schedule" in user_message or "task" in user_message:
        return jsonify({"response": get_schedule().json})

    response_text = talk_with_gemini(user_message)
    
    extracted_info = ""
    if detected_entities["PERSON"]:
        extracted_info += f"👤 Person(s): {', '.join(detected_entities['PERSON'])}\n"
    if detected_entities["DATE"]:
        extracted_info += f"📅 Date: {detected_entities['DATE']}\n"
    if detected_entities["TIME"]:
        extracted_info += f"⏰ Time: {detected_entities['TIME']}\n"

    return jsonify({
        "response": response_text.strip(),
        "entities": extracted_info if extracted_info else "No specific details detected."
    })

if __name__ == "__main__":
    app.run(debug=True)
