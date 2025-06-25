
import os
import subprocess
import time
import pyautogui
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()
API_KEY = os.getenv("API_KEY")

width , height = pyautogui.size()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

SCREENSHOT_DIR = 'screenshots'
TEMP_SCRIPT = 'temp_script.py'

# Ensure screenshot folder exists
def create_screenshot_folder():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"✔ Screenshot folder ready: {SCREENSHOT_DIR}")

def take_screenshot(name="screenshot"):
    try:
        timestamp = str(int(time.time()))
        path = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
        pyautogui.screenshot(path)
        print(f"📸 Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"❌ Screenshot error: {e}")
        return None

def delete_screenshots():
    try:
        if os.path.exists(SCREENSHOT_DIR):
            for file in os.listdir(SCREENSHOT_DIR):
                os.remove(os.path.join(SCREENSHOT_DIR, file))
            print(f"🧹 Deleted all screenshots in {SCREENSHOT_DIR}")
    except Exception as e:
        print(f"❌ Failed to delete screenshots: {e}")




# Prompt for task breakdown
def generate_analysis(user_prompt: str ) -> str:
    prompt = f"""
You are an expert AI assistant specializing in translating user instructions into step-by-step actions for desktop and browser automation.

Your job is to interpret the following natural language task:

"{user_prompt}"

🖥️ SCREEN RESOLUTION:
- The user's screen size is {width}x{height}. Use this for mouse positioning and screen-relative actions.
- Use pyautogui.locateOnScreen() with confidence threshold (e.g., 0.8) when clicking UI elements
 - Do not use hardcoded (x, y) coordinates unless it's for a fixed location like bottom-right of screen
 


🎯 OBJECTIVE:
Break down the task into **clear, executable steps** suitable for GUI automation using Python tools like **PyAutoGUI**, **web browsers**, and **screen interaction libraries**.

⚠️ INSTRUCTIONS — FOLLOW THESE RULES STRICTLY:

1. ❌ DO NOT generate or describe any Python code.
2. ✅ Describe what needs to happen, not how it's coded.
3. ✍️ Use simple, plain English. Be very clear and detailed.
4. 🧠 Think like a robot controlling a screen — every interaction must be possible using mouse, keyboard, or screen recognition.
5. ✅ All steps should be **sequential** and **explicit** — no guessing or assuming.

🔧 FOR EACH STEP, INCLUDE:
- 🎯 Exact mouse or keyboard actions (e.g., "press Win + D", "type 'notepad'")
- 🧭 GUI interactions (e.g., "click the Gmail inbox tab", "scroll down")
- 🕒 Wait times (e.g., "wait 3 seconds after clicking")
- 📸 When to take screenshots (e.g., "take a screenshot after the Gmail inbox appears")

🌐 FOR BROWSER TASKS:
- Open the browser (e.g., Chrome, Edge)
- Navigate to specific URLs (e.g., https://mail.google.com)
- Perform search queries or click specific links
- Identify elements by visible labels or positions
- Handle popups or login screens if needed

📌 EXAMPLES OF GOOD STEPS:
- Press Win + D to show the desktop.
- Press the Windows key, type "chrome", then press Enter.
- Wait 3 seconds for Chrome to open.
- In the address bar, type "https://mail.google.com" and press Enter.
- Wait for Gmail to load.
- Take a screenshot of the inbox screen.
- Click on the first (most recent) email in the list.
- Wait 2 seconds.
- Take a screenshot of the opened email.

🚨 NOTE:
- This will be passed to a code-generating AI that will create Python automation scripts.
- So your steps must be reliable and suitable for automation via screen control.

🧾 TASK TO ANALYZE:
{user_prompt}

Now provide a detailed breakdown of every step required to complete the task above. Be as clear and literal as possible. 
"""

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "Task Analyzer"},
    )
    return response.choices[0].message.content.strip()





# Prompt for actual Python code generation
def generate_code_from_analysis(task_description: str) -> str:
    prompt = f"""
Write a Python automation script using pyautogui and time, based on the task below:

"{task_description}"

⚠️ Only output valid, complete Python code.
- Use pyautogui, time, os
- Create screenshots folder at the start
- Take screenshots after each action
- Use try/except for file and GUI ops
- No markdown, no extra text
"""
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "Code Generator"},
    )
    return response.choices[0].message.content.strip()



# New: Improve the generated Python code using a second AI model
def improve_generated_code(raw_code: str) -> str:
    prompt = f"""
You are a senior Python automation engineer.

Improve the following automation script written using PyAutoGUI. Your job is to:
- Make it more reliable and robust
- Add better error handling
- Ensure each step has a small delay (e.g., time.sleep)
- Make sure screenshots are taken after each action
- Keep all functionality identical

DO NOT include markdown, explanations, or anything other than valid Python code.

Original Code:
{raw_code}
"""
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",  # second model
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "Code Improver"},
    )
    return response.choices[0].message.content.strip()

# Executes the AI-generated Python code
def execute_generated_code(code: str) -> str:
    try:
        # Clean markdown if present
        code = code.replace("```python", "").replace("```", "").strip()

        with open(TEMP_SCRIPT, "w", encoding="utf-8") as f:
            f.write(code)
        print("🚀 improving  the script.... ")

        result = subprocess.run(
            [os.sys.executable, TEMP_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60
        )

        if os.path.exists(TEMP_SCRIPT):
            os.remove(TEMP_SCRIPT)

        delete_screenshots()

        if result.stderr:
            print(f"❗ Error during execution:\n{result.stderr}")
            return f"Execution failed:\n{result.stderr}"
        return f"Execution successful:\n{result.stdout}"
    except Exception as e:
        return f"Error executing code: {str(e)}"

@app.route("/submit", methods=["POST"])
def handle_input():
    try:
        data = request.get_json()
        user_input = data.get("text", "")
        print("🎯 User request:", user_input)

        create_screenshot_folder()

        analysis = generate_analysis(user_input)
        print("📋 Task Analysis")

        code = generate_code_from_analysis(analysis)
        print("📄 generating the first code ...")  # Preview first 200 chars
        
        improved_code = improve_generated_code(code)
        print("✅ improving the code ...")  # Preview first 200 chars

        result = execute_generated_code(improved_code)
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


