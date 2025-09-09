"""
Quick API Test
==============

Test the API with correct request format.
"""

from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

# Test the API with correct format
response = client.post(
    "/api/webhook",
    json={
        "sender": "test_user_123",
        "recipient": "test_page",
        "text": "Hi, I need skincare help"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
