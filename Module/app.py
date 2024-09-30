import requests

API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder2-15b"
headers = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
    "inputs": "def fibonacci(n):",
})
print(output[0]['generated_text'])