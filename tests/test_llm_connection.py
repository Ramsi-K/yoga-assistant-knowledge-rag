"""Quick test to verify LLM API connection."""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Add yoga_assistant to path
sys.path.insert(0, "yoga_assistant")

print("Testing LLM API connection...")
print(f"API Key present: {bool(os.getenv('LLM_API_KEY'))}")
print(f"Base URL: {os.getenv('LLM_BASE_URL')}")
print(f"Model: {os.getenv('LLM_MODEL')}")

try:
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.hyperbolic.xyz/v1"),
    )

    print("\nSending test request...")
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3"),
        messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
        max_tokens=10,
        temperature=0.3,
        timeout=10.0,
    )

    print("✓ Connection successful!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")

except Exception as e:
    print(f"✗ Connection failed: {str(e)}")
    import traceback

    traceback.print_exc()
