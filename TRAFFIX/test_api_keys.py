#!/usr/bin/env python3
"""
Test script to verify API keys are loaded correctly
(Without exposing the actual keys)
"""
import os
from dotenv import load_dotenv

def test_api_keys():
    """Test that API keys are loaded from .env file"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔐 API Keys Configuration Test")
    print("=" * 40)
    
    # Test each API key
    apis = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Tavily": os.getenv("TAVILY_API_KEY"),
        "LangSmith": os.getenv("LANGSMITH_API_KEY"),
        "Cohere": os.getenv("COHERE_API_KEY"),
        "RAGAS": os.getenv("RAGAS_API_KEY")
    }
    
    all_good = True
    
    for api_name, key in apis.items():
        if key and key != "your-actual-key-here" and len(key) > 10:
            print(f"✅ {api_name}: Configured")
        elif key == "your-actual-key-here" or not key:
            print(f"❌ {api_name}: Not configured")
            if api_name in ["OpenAI", "Tavily"]:
                all_good = False
        else:
            print(f"⚠️  {api_name}: Key too short")
            if api_name in ["OpenAI", "Tavily"]:
                all_good = False
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 All required API keys are configured!")
        print("🚀 You can now run the Traffix application")
    else:
        print("⚠️  Some required API keys are missing")
        print("📝 Please check your .env file")
    
    # Test environment loading
    print(f"\n📊 Environment Status:")
    print(f"   Qdrant URL: {os.getenv('QDRANT_URL', 'Not set')}")
    print(f"   Log Level: {os.getenv('LOG_LEVEL', 'Not set')}")
    print(f"   Project: {os.getenv('LANGSMITH_PROJECT', 'Not set')}")

if __name__ == "__main__":
    test_api_keys()
