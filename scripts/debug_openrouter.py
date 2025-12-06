import os
import openai
import sys

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip()

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key starts with: {api_key[:15]}...")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

try:
    print("Sending request to OpenRouter...")
    response = client.chat.completions.create(
        model="deepseek/deepseek-r1",
        messages=[
            {"role": "user", "content": "Hello, simply reply with 'Hello World'"}
        ]
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
