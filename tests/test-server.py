import requests
import json

# Test the server
BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("Test 1: Health Check")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Example prompt from the exercise
print("Test 2: Example Prompt")
test_prompt = {
    "prompt": "Generate a random number. If the number is less than 0.5, multiply it by 0.1234567, otherwise divide it by 1.1234567. Generate another random number, get the square root of it, and then multiply it by the previous result."
}

response = requests.post(
    f"{BASE_URL}/",
    headers={"Content-Type": "application/json"},
    json=test_prompt
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Result: {result['result']}")
    print(f"Random Numbers: {result['random_integers']}")
    print(f"Number of random numbers: {len(result['random_integers'])}")
else:
    print(f"Error: {response.text}")

# Test 3: Simple prompt
print("\nTest 3: Simple Prompt")
simple_prompt = {
    "prompt": "Generate a random number. Multiply it by 2."
}

response = requests.post(
    f"{BASE_URL}/",
    headers={"Content-Type": "application/json"},
    json=simple_prompt
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Result: {result['result']}")
    print(f"Random Numbers: {result['random_integers']}")
else:
    print(f"Error: {response.text}")