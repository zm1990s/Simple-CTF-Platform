#!/usr/bin/env python3
"""
Test script to verify CTF platform functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_homepage():
    """Test homepage access"""
    print("Testing homepage...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print("✅ Homepage accessible")

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    # This will fail if no competitions exist, but shows the endpoint works
    response = requests.get(f"{BASE_URL}/api/leaderboard/1")
    print(f"API Leaderboard status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API working, leaderboard data: {json.dumps(data, indent=2)}")
    elif response.status_code == 404:
        print("⚠️  No competition found (expected if database is empty)")
    else:
        print(f"❌ Unexpected response: {response.status_code}")

def test_registration():
    """Test user registration"""
    print("\nTesting user registration...")
    
    # Note: This will fail if user already exists
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", data=user_data, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print("✅ Registration endpoint working")
    else:
        print(f"Registration status: {response.status_code}")

def main():
    """Run all tests"""
    print("="*50)
    print("CTF Platform Test Suite")
    print("="*50)
    
    try:
        test_homepage()
        test_api_endpoints()
        test_registration()
        
        print("\n" + "="*50)
        print("✅ Basic tests completed!")
        print("="*50)
        print("\nNote: Some tests may show warnings if database is empty.")
        print("This is normal for a fresh installation.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to the server!")
        print("Make sure the application is running on", BASE_URL)
        print("\nStart the server with:")
        print("  python app.py")
        print("  OR")
        print("  docker compose up")

if __name__ == '__main__':
    main()
