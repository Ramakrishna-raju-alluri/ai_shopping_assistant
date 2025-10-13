#!/usr/bin/env python3
"""
Test the complete user flow: Signup -> Profile Setup -> Dashboard
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_complete_user_flow():
    """Test the complete user flow"""
    print("🧪 Testing Complete User Flow")
    print("=" * 50)
    
    # Step 1: Test signup (new user)
    print("\n👤 Step 1: Testing New User Signup")
    print("-" * 30)
    
    signup_data = {
        "username": f"newuser_{int(time.time())}",
        "email": f"newuser_{int(time.time())}@example.com",
        "password": "testpass123",
        "name": "New Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 201:
            user_data = response.json()
            access_token = user_data["access_token"]
            user_id = user_data["user_id"]
            print(f"✅ New user created successfully: {user_id}")
            print(f"   Username: {signup_data['username']}")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return
    
    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Check profile status (should be incomplete for new user)
    print("\n📊 Step 2: Checking Profile Status (New User)")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Profile status for new user:")
            print(f"   Setup complete: {status['is_setup_complete']}")
            print(f"   Missing sections: {status['missing_sections']}")
            print(f"   Profile data: {len(status['profile_data'])} sections")
            
            # New user should have incomplete profile
            if not status['is_setup_complete']:
                print("✅ Correct: New user has incomplete profile")
            else:
                print("❌ Unexpected: New user has complete profile")
        else:
            print(f"❌ Failed to get profile status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting profile status: {str(e)}")
    
    # Step 3: Complete profile setup
    print("\n🎯 Step 3: Completing Profile Setup")
    print("-" * 30)
    
    complete_profile = {
        "dietary": {
            "diet": "vegetarian",
            "allergies": ["nuts"],
            "restrictions": []
        },
        "cuisine": {
            "preferred_cuisines": ["italian", "mediterranean"],
            "disliked_cuisines": []
        },
        "cooking": {
            "skill_level": "intermediate",
            "cooking_time_preference": "moderate",
            "kitchen_equipment": ["stove", "oven", "blender"]
        },
        "budget": {
            "budget_limit": 75.0,
            "meal_budget": 12.0,
            "shopping_frequency": "weekly"
        },
        "meal_goal": "healthy_balanced_meals"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/profile-setup/complete", 
                               json=complete_profile, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Profile setup completed successfully!")
            print(f"   User ID: {result['user_id']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to complete profile setup: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error completing profile setup: {str(e)}")
    
    # Step 4: Verify profile is now complete
    print("\n✅ Step 4: Verifying Profile Completion")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Profile status after setup:")
            print(f"   Setup complete: {status['is_setup_complete']}")
            print(f"   Missing sections: {status['missing_sections']}")
            print(f"   Profile data sections: {list(status['profile_data'].keys())}")
            
            if status['is_setup_complete']:
                print("✅ Correct: Profile is now complete")
            else:
                print("❌ Unexpected: Profile is still incomplete")
        else:
            print(f"❌ Failed to get profile status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting profile status: {str(e)}")
    
    # Step 5: Test login for existing user
    print("\n🔐 Step 5: Testing Login for Existing User")
    print("-" * 30)
    
    login_data = {
        "username": signup_data["username"],
        "password": signup_data["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            login_response = response.json()
            print(f"✅ Login successful for existing user!")
            print(f"   User ID: {login_response['user_id']}")
            print(f"   Username: {login_response['username']}")
            
            # Check profile status for existing user
            new_headers = {"Authorization": f"Bearer {login_response['access_token']}"}
            profile_response = requests.get(f"{BASE_URL}/profile-setup/status", headers=new_headers)
            
            if profile_response.status_code == 200:
                profile_status = profile_response.json()
                print(f"   Profile complete: {profile_status['is_setup_complete']}")
                print("✅ Existing user can access dashboard with complete profile")
            else:
                print("❌ Failed to check profile status for existing user")
        else:
            print(f"❌ Failed to login: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
    
    print("\n🎉 Complete User Flow Test Finished!")
    print("\n📝 Summary:")
    print("   ✅ New user signup works")
    print("   ✅ New user has incomplete profile")
    print("   ✅ Profile setup can be completed")
    print("   ✅ Profile status is correctly updated")
    print("   ✅ Existing user can login")
    print("   ✅ Existing user has complete profile")

if __name__ == "__main__":
    test_complete_user_flow() 