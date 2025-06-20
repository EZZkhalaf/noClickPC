
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


def main(user_prompt):
    try:
        
        prompt = (
                "You are a code generation assistant. "
                "Only return raw, valid, and executable Windows .bat or CMD script code that does the following task:\n"
                f"{user_prompt}\n\n"
                " DO NOT include any explanations, markdown code blocks, comments, or anything else.\n"
                "ONLY respond with Windows-compatible .bat commands (no PowerShell, no markdown)."
            )


        load_dotenv()
        apiKey = os.getenv('API_KEY')
        if not apiKey:
            raise ValueError("API_KEY not found in .env file. Please set it.")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=apiKey,
        )

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "fatcat",
                "X-Title": "fatcat2",
            },
            model="mistralai/mistral-7b-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        response_code = completion.choices[0].message.content
        print("The response is:\n", response_code, "\n")
        # Clean up lines: remove markdown formatting like `` or `
        lines = [line.replace('`', '').strip() for line in response_code.strip().split('\n') if line.strip()]

        file_name = "fatcat022.bat"
        file_path = os.path.join(os.getcwd(), file_name)

        print("The file is being created and executed...")

        with open(file_path, 'w') as file:
            file.write("\n".join(lines))

        print(f"File '{file_name}' created successfully at {file_path}")

        result = subprocess.run([file_path], capture_output=True, text=True)
        if result.stderr:
            print("Errors:", result.stderr)

        # Optional cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_name}' deleted successfully.")

        return "Command executed successfully."

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
