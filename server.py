
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
You are an expert AI planner responsible for converting high-level user instructions into clear, structured, step-by-step actions for Python-based GUI and browser automation.

Your job is to interpret the following natural language task:

"{user_prompt}"

🎯 OBJECTIVE:
Break the task down into **precise, literal steps** that a Python script could execute using automation tools like **PyAutoGUI**, **web browser control**, and **screen-based interaction libraries**.

These steps will be used as the input for a separate AI that writes the actual Python code — so your steps must be clean, complete, and easily translatable to code.

🖥️ SCREEN DETAILS:
- The user's screen size is {width}x{height}. Use this to guide relative positioning.
- Use screen recognition via `pyautogui.locateOnScreen()` for clicking UI elements.
- Do **not** rely on hardcoded pixel coordinates unless referencing a fixed part of the screen (e.g., taskbar or bottom-right).

⚠️ RULES FOR STEP GENERATION:

1. ❌ DO NOT generate or describe any Python code.
2. ✅ DO provide a precise sequence of steps describing **what should happen** on screen.
3. ✅ Use simple, literal, plain English to describe each action.
4. 🧠 Think like an automation robot — only mouse, keyboard, and screen elements are available.
5. ✅ Steps must be clear, atomic, and explicitly executable — no assumptions, no interpretation.
6. ✅ Make sure the result is **suitable for a Python code generation system** to act on.

🔧 FOR EACH STEP, INCLUDE:
- 🎯 The exact mouse or keyboard action (e.g., "Press the Windows key", "Type 'chrome'")
- 🧭 The target of interaction (e.g., "Click the Gmail inbox tab", "Click the search bar")
- 🕒 Wait times (e.g., "Wait 3 seconds after clicking")
- 📸 Screenshot moments (e.g., "Take a screenshot after the Gmail inbox appears")

🌐 FOR BROWSER TASKS:
- Open the browser (Chrome is preferred)
- Navigate to specific URLs or Google Search queries
- Click specific links or buttons using visual labels or positions
- Handle login screens, pop-ups, or scrollable content if necessary

📌 EXAMPLES OF GOOD OUTPUT STEPS:
- Press the Windows key, type "chrome", and press Enter.
- Wait 2 seconds for Chrome to open.
- In the address bar, type "https://mail.google.com" and press Enter.
- Wait for Gmail to load fully.
- Take a screenshot of the inbox view.
- Click the most recent email in the list.
- Wait 2 seconds.
- Take a screenshot of the opened email.

🚨 FINAL NOTE:
- The next system will write Python code based on the exact steps you output.
- Be careful, literal, and detailed — the quality of the automation depends entirely on your clarity and precision.

🧾 TASK TO ANALYZE:
{user_prompt}

Now provide a complete, detailed breakdown of every required action to fulfill the task above. Be as clear and step-by-step as possible.
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
Write a complete Python automation script using only the following libraries: pyautogui, time, os.

Your script should perform the automation described below, following all instructions step by step:

"{task_description}"

📂 GENERAL REQUIREMENTS:
- Ensure a folder named 'screenshots' exists at the beginning of the script. Create it if it doesn't.
- After **every action** (e.g., clicking, typing, opening something), take a screenshot and save it to the 'screenshots' folder.
- Use `time.sleep()` after every significant action to allow the GUI to respond.

🖱️ MOUSE AND GUI INTERACTION RULES:
- Never use hardcoded coordinates (e.g., pyautogui.moveTo(100, 200)).
- Always use `pyautogui.locateCenterOnScreen('filename.png', confidence=0.8)` to find and interact with screen elements.
- Before moving or clicking, always check that `locateCenterOnScreen()` returned a valid result (not None).
- If the element is not found:
  - Handle it gracefully with a `try/except` or `if` check.
  - Optionally take a screenshot to log the failure.

🛠️ CODE QUALITY RULES:
- Wrap all file system and GUI operations in `try/except` blocks.
- Organize code clearly, in sequential steps according to the task.
- Do not include any comments, markdown, or explanations — only output valid Python code.

✅ OUTPUT ONLY:
Only return raw, executable Python code. No text, headers, or formatting.

Begin your response now with valid Python code that completes the task below:

"{task_description}"
"""


    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "Code Generator"},
    )
    return response.choices[0].message.content.strip()



# New: Improve the generated Python code using a second AI model
def improve_generated_code(raw_code: str , task : str) -> str:
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
and here is the task that the user wants to do : 
{task}
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
        

        result = subprocess.run(
            [os.sys.executable, TEMP_SCRIPT],
            capture_output=True,
            text=True,
            timeout=80
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
        
        improved_code = improve_generated_code(code , user_input)
        print("✅ improving the code ...")  # Preview first 200 chars

        result = execute_generated_code(improved_code)
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

