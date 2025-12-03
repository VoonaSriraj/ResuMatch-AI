import requests
import time

def test_linkedin_connection():
    """Test LinkedIn connection flow"""
    base_url = "http://localhost:8001"
    headers = {"Authorization": "Bearer dev"}
    
    print("🔍 Testing LinkedIn Connection...")
    
    # Test 1: Check backend health
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Test 2: Check LinkedIn status
    try:
        response = requests.get(f"{base_url}/api/linkedin/status", headers=headers, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ LinkedIn Status: Connected={status.get('connected', False)}")
            return True
        else:
            print(f"❌ LinkedIn status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LinkedIn status check failed: {e}")
        return False

if __name__ == "__main__":
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(10)
    
    success = test_linkedin_connection()
    if success:
        print("\n🎉 LinkedIn connection test completed successfully!")
    else:
        print("\n❌ LinkedIn connection test failed!")
