import requests
import json

BASE_URL = "http://localhost:8000" # Change to Railway URL if testing remote

def test_send_message():
    url = f"{BASE_URL}/chat/send"
    payload = {
        "sender_id": "1", # Using string to test flexibility
        "receiver_id": "2",
        "content": "Test message from verification script",
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.statusCode}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: This requires the backend to be running and users with IDs 1 and 2 to exist.
    # If using Railway, replace BASE_URL with the actual production URL.
    print("Testing chat API...")
    test_send_message()
