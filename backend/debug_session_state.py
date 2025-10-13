#!/usr/bin/env python3
"""
Debug Session State
Simple script to debug session state and understand feedback flow
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def debug_session_state():
    """Debug session state and feedback flow"""
    
    print("🐛 DEBUGGING SESSION STATE")
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
        "message": "Plan 3 meals under $50"
    }
    
    chat_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    if chat_response.status_code != 200:
        print(f"❌ Chat failed: {chat_response.status_code}")
        return
    
    session_id = chat_response.json()["session_id"]
    print(f"✅ Chat session: {session_id}")
    
    # Check initial session state
    print(f"\n📊 Initial session state:")
    print(f"   Step: {chat_response.json().get('step')}")
    print(f"   Requires confirmation: {chat_response.json().get('requires_confirmation')}")
    print(f"   Requires input: {chat_response.json().get('requires_input')}")
    print(f"   Message: {chat_response.json().get('message', '')[:100]}...")
    
    # Confirm to proceed
    confirm_data = {"session_id": session_id, "confirmed": True}
    confirm_response = requests.post(f"{BASE_URL}/confirm", json=confirm_data, headers=headers)
    
    print(f"\n📊 After confirmation:")
    print(f"   Step: {confirm_response.json().get('step')}")
    print(f"   Requires confirmation: {confirm_response.json().get('requires_confirmation')}")
    print(f"   Requires input: {confirm_response.json().get('requires_input')}")
    
    # Continue until we reach feedback
    step_count = 0
    while step_count < 10:  # Limit to avoid infinite loop
        step_count += 1
        last_response = confirm_response.json()
        current_step = last_response.get("step", "")
        
        print(f"\n🔄 Step {step_count}: {current_step}")
        
        if current_step == "final_cart_ready":
            print("🎯 Reached feedback collection point!")
            break
        elif last_response.get("requires_confirmation"):
            print("   → Confirming step...")
            confirm_data = {"session_id": session_id, "confirmed": True}
            confirm_response = requests.post(f"{BASE_URL}/confirm", json=confirm_data, headers=headers)
        elif last_response.get("requires_input"):
            print("   → Providing input...")
            input_data = {"session_id": session_id, "input": "test input"}
            confirm_response = requests.post(f"{BASE_URL}/input", json=input_data, headers=headers)
        else:
            print("   → Sending continue message...")
            chat_data = {"message": "continue", "session_id": session_id}
            confirm_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
    
    # Start feedback collection
    print(f"\n🎯 Starting feedback collection...")
    feedback_start_data = {"session_id": session_id, "confirmed": True}
    feedback_response = requests.post(f"{BASE_URL}/collect-feedback", json=feedback_start_data, headers=headers)
    
    if feedback_response.status_code == 200:
        feedback_data = feedback_response.json()
        print(f"✅ Feedback collection started:")
        print(f"   Step: {feedback_data.get('step')}")
        print(f"   Requires input: {feedback_data.get('requires_input')}")
        print(f"   Input type: {feedback_data.get('input_type')}")
        print(f"   Input prompt: {feedback_data.get('input_prompt')}")
        
        # Test rating input
        print(f"\n🧪 Testing rating input '3'...")
        rating_data = {"message": "3", "session_id": session_id}
        rating_response = requests.post(f"{BASE_URL}/chat", json=rating_data, headers=headers)
        
        if rating_response.status_code == 200:
            rating_result = rating_response.json()
            print(f"✅ Rating response:")
            print(f"   Step: {rating_result.get('step')}")
            print(f"   Message: {rating_result.get('message', '')[:100]}...")
            print(f"   Requires input: {rating_result.get('requires_input')}")
            
            if rating_result.get('step', '').startswith('feedback_'):
                print("✅ SUCCESS: Rating handled as feedback!")
            else:
                print("❌ FAILURE: Rating sent to LLM!")
        else:
            print(f"❌ Rating input failed: {rating_response.status_code}")
    else:
        print(f"❌ Feedback collection failed: {feedback_response.status_code}")

if __name__ == "__main__":
    debug_session_state() 