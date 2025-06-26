import os
import subprocess
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/submit', methods=['POST'])
def handle_input():
    data = request.get_json()
    user_input = data.get('text', '')
    print("Received from app:", user_input)

    result_message = main(user_input)  # Call your main function and pass input

    return jsonify({'message': result_message})


def generate_python_code_from_prompt(user_prompt: str) -> str:
    load_dotenv()
    apiKey = os.getenv('API_KEY')
    if not apiKey:
        raise ValueError("API_KEY not found in .env file. Please set it.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=apiKey,
    )

    # Step 1: Task analysis prompt (no code generation)
    prompt1 = f"""
You are a task analysis assistant specializing in **keyboard-only** automation using Python tools such as PyAutoGUI.

Your job is to:
1. Read the user's natural language input.
2. Analyze the user’s goal using only **keyboard actions**, such as typing text, pressing individual keys, using keyboard shortcuts (e.g., Ctrl+C, Alt+Tab), and executing command-line-style inputs.
3. Break the task into a clear, step-by-step plan using only **keyboard-based automation**, suitable for generating Python code later.

🚫 DO NOT:
- Write or generate any Python code.
- Mention mouse actions, GUI clicking, or visual detection.
- Include Python syntax, imports, or implementation specifics.
- Ask the user for clarification.

✅ DO:
- Focus only on keyboard and command-line interactions (e.g., Windows key, typing commands, Enter key, tab navigation).
- Describe key combinations explicitly (e.g., "Press Ctrl+S", "Hold Shift and press Tab").
- Use plain English and literal steps suitable for another AI to generate code later.
- Include wait or pause steps when needed for smooth automation (e.g., waiting after launching an app or opening a menu).

📌 If the task involves opening programs, navigating menus, modifying files, or executing commands, describe how it would be done using **keyboard shortcuts and typing alone**.

User Input: {user_prompt}

Now provide a complete, detailed breakdown of the task using only keyboard actions and command-line-like steps. Be precise, literal, and structured, so the next AI can convert it into automation code.
"""
    response1 = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>",
        },
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt1}]
    )
    task_description = response1.choices[0].message.content.strip()

    # Step 2: Python code generation prompt
    prompt2 = f"""
You are a Python code generator.

Your task is to write valid Python code based on the following task description provided by another AI.

⚠️ IMPORTANT RULES:
- Return ONLY valid, complete, and executable Python code.
-the google / chrome path is "C:\Program Files\Google\Chrome\Application\chrome.exe"
- Include all necessary import statements.
- Include appropriate wait or delay commands especially when deleting files or performing critical operations.
- Do NOT include any explanations, comments, or extra formatting.
- Assume this code will be saved as a temporary .py file and executed immediately.
-you have to wait for a little time when you delete some files or something if needed to 

Task Description:
{task_description}

Generate the exact Python code to perform the described task.
"""

    response2 = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>",
        },
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt2}]
    )
    python_code = response2.choices[0].message.content.strip()
    return python_code



def main(user_prompt):
    try:
        python_code = generate_python_code_from_prompt(user_prompt)

        # Clean the AI output: remove markdown backticks and 'python' header if present
        clean_code = python_code.strip()
        if clean_code.startswith("```"):
            clean_code = clean_code.strip("`")
        lines = clean_code.splitlines()
        if lines and lines[0].lower().strip() == "python":
            lines.pop(0)
        cleaned_code = "\n".join(lines)

        file_name = "temp_script.py"
        file_path = os.path.join(os.getcwd(), file_name)

        print("Creating and executing Python script...")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_code)

        print(f"File '{file_name}' created successfully at {file_path}")

        # Execute the Python file with the current interpreter
        result = subprocess.run(
            [os.sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        errors = result.stderr

        if errors:
            print("Errors during execution:", errors)

        # Clean up the temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_name}' deleted successfully.")

        if errors:
            return f"Execution finished with errors:\n{errors}"
        else:
            return f"Execution successful:\n{output}"

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)