import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get API token from environment variable
API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not API_TOKEN:
    raise ValueError("HUGGINGFACEHUB_API_TOKEN not found in .env file")

# Using the Salesforce/codegen-350M-mono model
API_URL = "https://api-inference.huggingface.co/models/Salesforce/codegen-350M-mono"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def generate_code(prompt: str, max_length: int = 256) -> str:
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_length,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "return_full_text": False
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    result = response.json()
    
    if isinstance(result, list) and len(result) > 0:
        generated_code = result[0].get('generated_text', '')
        return generated_code.strip()
    else:
        raise Exception("Unexpected API response format")

# Example usage
prompt = "Write a Python function to calculate the factorial of a number"
try:
    generated_code = generate_code(prompt)
    print(f"Generated code:\n{generated_code}")
except Exception as e:
    print(f"An error occurred: {str(e)}")