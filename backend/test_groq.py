import os
import sys
from groq import Groq

def test_groq_api(api_key: str):
    try:
        print("Testing Groq API connection...")
        
        # Initialize the Groq client
        client = Groq(api_key=api_key)
        
        # Make a test API call
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Hello! This is a test message to verify API connectivity."
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=50,
            temperature=0.7,
        )
        
        # Print the response
        print("\n✅ API Connection Successful!")
        print("Response from Groq API:")
        print("-" * 40)
        print(response.choices[0].message.content)
        print("-" * 40)
        return True
        
    except Exception as e:
        print("\n❌ API Connection Failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Get API key from environment variable or direct input
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        api_key = input("Please enter your Groq API key: ").strip()
    
    test_groq_api(api_key)