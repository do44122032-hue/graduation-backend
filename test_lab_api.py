import requests
import os

BASE_URL = "http://localhost:8000"

def test_upload_lab_result():
    url = f"{BASE_URL}/lab/upload"
    # Note: Requires a user with ID 1 to exist. Adjust as needed.
    data = {"uid": "1"}
    
    # Create a dummy image file if it doesn't exist
    dummy_image = "test_lab.jpg"
    if not os.path.exists(dummy_image):
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(dummy_image)

    try:
        with open(dummy_image, "rb") as f:
            files = {"file": (dummy_image, f, "image/jpeg")}
            response = requests.post(url, data=data, files=files)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Lab Upload API...")
    test_upload_lab_result()
