#!/usr/bin/env python3
"""
Debug Feedback Collection
Simple script to debug the feedback collection issue
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def debug_feedback():
    """Debug the feedback collection issue"""
    
    print("🐛 DEBUGGING FEEDBACK COLLECTION")
    print("=" * 40)
    
    # Login
    login_data = {
        "username": "test_user_001",
        "password": "password123"
    }
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    user_id = login_response.json()["user_id"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Logged in as: {user_id}")
    
    # Start chat
    chat_data = {
        "user_id": user_id,
        "message": "Plan 3 meals under $50"
    }
    
    chat_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    if chat_response.status_code != 200:
        print(f"❌ Chat failed: {chat_response.status_code}")
        return
    
    session_id = chat_response.json()["session_id"]
    print(f"✅ Chat session: {session_id}")
    
    # Get session info
    session_response = requests.get(f"{BASE_URL}/sessions/{session_id}", headers=headers)
    if session_response.status_code == 200:
        session_info = session_response.json()
        print(f"✅ Session info: {session_info}")
    else:
        print(f"❌ Session info failed: {session_response.status_code}")
    
    # Try to call collect-feedback directly
    confirm_data = {
        "session_id": session_id,
        "user_id": user_id,
        "confirmed": True
    }
    
    print("\n🔍 Testing collect-feedback endpoint...")
    feedback_response = requests.post(f"{BASE_URL}/collect-feedback", json=confirm_data, headers=headers)
    print(f"Status: {feedback_response.status_code}")
    
    if feedback_response.status_code != 200:
        print(f"❌ Error response: {feedback_response.text}")
    else:
        print(f"✅ Success response: {feedback_response.json()}")

if __name__ == "__main__":
    debug_feedback() 