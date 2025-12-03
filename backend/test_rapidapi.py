#!/usr/bin/env python3
"""
Quick test script to verify RapidAPI LinkedIn Jobs integration
"""

import requests
import os
from typing import List, Dict, Any

def test_rapidapi_linkedin_jobs(api_key: str = None):
    """Test RapidAPI LinkedIn Jobs API"""
    
    if not api_key:
        print("❌ No RapidAPI key provided")
        print("\n🔑 To get your RapidAPI key:")
        print("1. Go to https://rapidapi.com/")
        print("2. Sign up for free")
        print("3. Search for 'LinkedIn Jobs Search API'")
        print("4. Subscribe to the API (usually free tier available)")
        print("5. Copy your API key")
        print("\nThen run: python test_rapidapi.py YOUR_API_KEY")
        return False
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-job-search-api.p.rapidapi.com"
    }
    
    params = {
        "offset": 0,
        "description_type": "text"
    }
    
    try:
        print("🔍 Testing RapidAPI LinkedIn Jobs API...")
        response = requests.get(
            "https://linkedin-job-search-api.p.rapidapi.com/active-jb-1h",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"✅ Success! Found {len(jobs)} jobs")
            
            for i, job in enumerate(jobs[:3], 1):
                print(f"\n{i}. {job.get('title', 'N/A')}")
                print(f"   Company: {job.get('company', 'N/A')}")
                print(f"   Location: {job.get('location', 'N/A')}")
                print(f"   URL: {job.get('apply_url', 'N/A')}")
            
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        test_rapidapi_linkedin_jobs(api_key)
    else:
        test_rapidapi_linkedin_jobs()
