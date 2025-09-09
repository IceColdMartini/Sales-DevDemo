#!/usr/bin/env python3
"""
Azure OpenAI API Key Test Script
================================

Tests if the Azure OpenAI API key is working correctly.
This script verifies the connection and basic functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_openai_connection():
    """Test Azure OpenAI API connection and functionality."""
    print("🔍 Testing Azure OpenAI API Key Configuration")
    print("=" * 50)

    # Check environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("OPENAI_API_VERSION")
    deployment_name = os.getenv("OPENAI_MODEL") or os.getenv("DEPLOYMENT_NAME")

    print(f"✅ API Key configured: {'Yes' if api_key else 'No'}")
    print(f"✅ Endpoint configured: {'Yes' if endpoint else 'No'}")
    print(f"✅ API Version: {api_version}")
    print(f"✅ Deployment/Model: {deployment_name}")

    if not all([api_key, endpoint, deployment_name]):
        print("\n❌ Missing required configuration!")
        return False

    # Mask API key for security
    masked_key = api_key[:10] + "..." + api_key[-10:] if len(api_key) > 20 else "***"
    print(f"🔑 API Key (masked): {masked_key}")

    try:
        # Try different import approaches for Azure OpenAI
        print("\n🔧 Initializing Azure OpenAI client...")

        # Try langchain_openai first (recommended)
        try:
            from langchain_openai import AzureChatOpenAI
            print("✅ Using langchain_openai.AzureChatOpenAI")
        except ImportError:
            try:
                from langchain_community.chat_models import AzureChatOpenAI
                print("⚠️ Using langchain_community.AzureChatOpenAI (deprecated)")
            except ImportError:
                try:
                    from langchain.chat_models import AzureChatOpenAI
                    print("⚠️ Using langchain.chat_models.AzureChatOpenAI (legacy)")
                except ImportError:
                    print("❌ No AzureChatOpenAI implementation found!")
                    return False

        # Initialize the client
        llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment_name,
            openai_api_version=api_version,
            openai_api_key=api_key,
            temperature=0.7,
            max_tokens=150
        )

        print("✅ Azure OpenAI client initialized successfully")

        # Test with a simple message
        print("\n🧪 Testing API call...")
        test_message = "Hello! Please respond with just 'Hello from Azure OpenAI!'"

        # Make the API call using the correct format
        response = llm.invoke(test_message)

        # Check response
        if response and hasattr(response, 'content'):
            content = response.content.strip()
            print(f"✅ API Response: {content}")

            if "Hello from Azure OpenAI" in content or "Hello" in content:
                print("🎉 SUCCESS: Azure OpenAI API is working correctly!")
                return True
            else:
                print("⚠️ API responded but with unexpected content")
                return True
        else:
            print("❌ API call failed - no valid response")
            return False

    except Exception as e:
        print(f"❌ API test failed: {str(e)}")

        # Provide specific error guidance
        error_str = str(e).lower()
        if "deployment" in error_str and "not found" in error_str:
            print("💡 Suggestion: Check if the deployment name is correct in your Azure OpenAI resource")
        elif "unauthorized" in error_str or "401" in error_str:
            print("💡 Suggestion: Check if the API key is correct and has proper permissions")
        elif "endpoint" in error_str:
            print("💡 Suggestion: Verify the Azure OpenAI endpoint URL")
        elif "timeout" in error_str:
            print("💡 Suggestion: Check network connectivity and Azure service status")

        return False

def test_langchain_integration():
    """Test if LangChain integration works with the current setup."""
    print("\n🔗 Testing LangChain Integration")
    print("=" * 30)

    try:
        from app.core.config import settings
        print("✅ Settings loaded from config")

        # Test if we can create a chain
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_template("Say hello to {name}")
        print("✅ ChatPromptTemplate created successfully")

        # Try to create a simple chain
        try:
            from langchain_openai import AzureChatOpenAI
            llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                openai_api_version=settings.OPENAI_API_VERSION,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                temperature=0.5,
                max_tokens=50
            )

            # Simple test without complex chaining
            test_prompt = "Say hello to the world in one sentence."
            result = llm.invoke(test_prompt)

            if result and hasattr(result, 'content'):
                print(f"✅ Chain test successful: {result.content[:50]}...")
                return True
            else:
                print("❌ Chain test failed - no valid response")
                return False

        except ImportError as ie:
            print(f"❌ Import error: {ie}")
            print("💡 Try updating LangChain: pip install -U langchain-openai")
            return False
        except Exception as e:
            print(f"❌ LangChain integration failed: {e}")
            return False

    except Exception as e:
        print(f"❌ LangChain integration setup failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Azure OpenAI API Key Test Suite")
    print("=" * 40)

    # Test basic connection
    basic_test = test_azure_openai_connection()

    # Test LangChain integration
    langchain_test = test_langchain_integration()

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 25)
    print(f"Basic API Connection: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"LangChain Integration: {'✅ PASS' if langchain_test else '❌ FAIL'}")

    if basic_test and langchain_test:
        print("\n🎉 ALL TESTS PASSED! Your Azure OpenAI setup is working correctly.")
        print("💡 Your conversation system should be able to generate responses.")
        return 0
    elif basic_test:
        print("\n⚠️ Basic API works but LangChain integration has issues.")
        print("💡 Check your LangChain configuration and imports.")
        return 1
    else:
        print("\n❌ API connection failed. Check your configuration.")
        print("💡 Verify your Azure OpenAI resource settings and API key.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
