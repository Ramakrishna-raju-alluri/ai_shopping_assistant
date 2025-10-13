#!/usr/bin/env python3
"""
Test Feedback Fix
Simple script to test that feedback inputs are properly handled and not sent to LLM
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_feedback_handling():
    """Test that feedback inputs are properly handled"""
    
    print("🧪 TESTING FEEDBACK HANDLING FIX")
    print("=" * 50)
    
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
    
    # Start a meal planning session to trigger feedback
    chat_data = {
        "message": "Plan 3 meals under $50"
    }
    
    print("\n1️⃣ Starting meal planning session...")
    chat_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    if chat_response.status_code != 200:
        print(f"❌ Chat failed: {chat_response.status_code}")
        return
    
    session_id = chat_response.json()["session_id"]
    print(f"✅ Chat session: {session_id}")
    
    # Go through the meal planning flow to reach feedback
    print("\n2️⃣ Going through meal planning flow...")
    
    # Confirm meal planning
    confirm_data = {"session_id": session_id, "confirmed": True}
    confirm_response = requests.post(f"{BASE_URL}/confirm", json=confirm_data, headers=headers)
    print(f"✅ Confirmed meal planning: {confirm_response.status_code}")
    
    # Continue through the flow until we reach feedback
    for i in range(5):  # Limit iterations to avoid infinite loop
        time.sleep(1)
        last_response = confirm_response.json()
        current_step = last_response.get("step", "")
        
        print(f"   Step {i+1}: {current_step}")
        
        if current_step == "final_cart_ready":
            # We've reached the feedback collection point
            break
        elif last_response.get("requires_confirmation"):
            # Confirm the step
            confirm_data = {"session_id": session_id, "confirmed": True}
            confirm_response = requests.post(f"{BASE_URL}/confirm", json=confirm_data, headers=headers)
        elif last_response.get("requires_input"):
            # Provide input
            input_data = {"session_id": session_id, "input": "test input"}
            confirm_response = requests.post(f"{BASE_URL}/input", json=input_data, headers=headers)
        else:
            # Send a message to continue
            chat_data = {"message": "continue", "session_id": session_id}
            confirm_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    
    # Now test feedback collection
    print("\n3️⃣ Testing feedback collection...")
    
    # Start feedback collection
    feedback_start_data = {"session_id": session_id, "confirmed": True}
    feedback_response = requests.post(f"{BASE_URL}/collect-feedback", json=feedback_start_data, headers=headers)
    
    if feedback_response.status_code != 200:
        print(f"❌ Feedback collection failed: {feedback_response.status_code}")
        return
    
    feedback_data = feedback_response.json()
    print(f"✅ Feedback collection started: {feedback_data.get('step')}")
    
    # Test rating input
    print("\n4️⃣ Testing rating input...")
    rating_data = {"message": "3", "session_id": session_id}
    rating_response = requests.post(f"{BASE_URL}/chat", json=rating_data, headers=headers)
    
    if rating_response.status_code != 200:
        print(f"❌ Rating input failed: {rating_response.status_code}")
        return
    
    rating_result = rating_response.json()
    print(f"✅ Rating response: {rating_result.get('step')}")
    print(f"✅ Message: {rating_result.get('message', '')[:100]}...")
    
    # Check if it's still in feedback mode
    if rating_result.get('step', '').startswith('feedback_'):
        print("✅ SUCCESS: Rating was handled as feedback, not sent to LLM!")
    else:
        print("❌ FAILURE: Rating was sent to LLM instead of being handled as feedback!")
    
    # Test liked items input
    print("\n5️⃣ Testing liked items input...")
    liked_data = {"message": "chicken, rice", "session_id": session_id}
    liked_response = requests.post(f"{BASE_URL}/chat", json=liked_data, headers=headers)
    
    if liked_response.status_code != 200:
        print(f"❌ Liked items input failed: {liked_response.status_code}")
        return
    
    liked_result = liked_response.json()
    print(f"✅ Liked items response: {liked_result.get('step')}")
    
    # Check if it's still in feedback mode
    if liked_result.get('step', '').startswith('feedback_'):
        print("✅ SUCCESS: Liked items were handled as feedback!")
    else:
        print("❌ FAILURE: Liked items were sent to LLM instead of being handled as feedback!")
    
    print("\n" + "=" * 50)
    print("🧪 FEEDBACK TESTING COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    test_feedback_handling() 