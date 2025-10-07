#!/usr/bin/env python3
"""
Demo script to run the Advanced RAG Evaluation
=============================================

This script demonstrates how to run the advanced RAG evaluation
with different configurations and provides a simple interface.
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'langchain',
        'ragas', 
        'sentence_transformers',
        'sklearn',
        'nltk'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements_advanced.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_api_key():
    """Check if OpenAI API key is set"""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OpenAI API key not found")
        print("💡 Set your API key with:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print("✅ OpenAI API key is set")
    return True

def check_data_directory():
    """Check if data directory exists and has PDF files"""
    data_path = Path("data")
    if not data_path.exists():
        print("❌ Data directory not found")
        print("💡 Create a 'data' directory and add PDF files")
        return False
    
    pdf_files = list(data_path.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in data directory")
        print("💡 Add PDF files to the 'data' directory")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF files in data directory")
    return True

def main():
    """Main demo function"""
    print("🚧 Advanced RAG Evaluation Demo 🚧")
    print("=" * 40)
    
    # Check prerequisites
    print("\n1. Checking prerequisites...")
    if not check_requirements():
        sys.exit(1)
    
    if not check_api_key():
        sys.exit(1)
    
    if not check_data_directory():
        sys.exit(1)
    
    print("\n2. All prerequisites met! 🎉")
    print("\n3. Running Advanced RAG Evaluation...")
    print("=" * 40)
    
    # Import and run the main script
    try:
        from advanced_rag_evaluation import main as run_evaluation
        run_evaluation()
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        print("\n💡 Make sure all dependencies are installed and API keys are set")
        sys.exit(1)

if __name__ == "__main__":
    main()

