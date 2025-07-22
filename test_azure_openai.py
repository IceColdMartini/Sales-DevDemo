#!/usr/bin/env python3
"""
Test Azure OpenAI connection with the provided credentials
"""
import os
from openai import AzureOpenAI

def test_azure_openai():
    try:
        # Initialize Azure OpenAI client with environment variables
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        )
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Just testing the connection."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ Azure OpenAI connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    test_azure_openai()
