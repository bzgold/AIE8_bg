#!/usr/bin/env python3
"""
Traffix Startup Script with Enhanced Technology Stack
"""
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

from config import settings
from tech_config import tech_settings
from services.vector_service import VectorService
from monitoring.evaluation_service import EvaluationService


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "openai", "langchain", "langgraph", "qdrant-client",
        "streamlit", "ragas", "langsmith", "plotly"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True


def check_services():
    """Check if required services are running"""
    print("🔍 Checking services...")
    
    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=tech_settings.qdrant_url)
        collections = client.get_collections()
        print("✅ Qdrant is running")
    except Exception as e:
        print(f"❌ Qdrant not accessible: {e}")
        print("Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Check OpenAI API
    if not tech_settings.openai_api_key:
        print("❌ OpenAI API key not set")
        print("Set OPENAI_API_KEY in .env file")
        return False
    print("✅ OpenAI API key configured")
    
    return True


async def initialize_vector_database():
    """Initialize vector database with collections"""
    print("🗄️ Initializing vector database...")
    
    try:
        vector_service = VectorService()
        stats = vector_service.get_collection_stats()
        print(f"✅ Vector database initialized - {stats.get('points_count', 0)} points")
        return True
    except Exception as e:
        print(f"❌ Vector database initialization failed: {e}")
        return False


async def initialize_monitoring():
    """Initialize monitoring and evaluation services"""
    print("📊 Initializing monitoring...")
    
    try:
        evaluation_service = EvaluationService()
        print("✅ Monitoring services initialized")
        return True
    except Exception as e:
        print(f"❌ Monitoring initialization failed: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "./reports",
        "./logs",
        "./templates",
        "./data",
        "./exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")


def setup_environment():
    """Setup environment variables and configuration"""
    print("⚙️ Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Traffix Configuration
OPENAI_API_KEY=your_openai_api_key_here
RITIS_API_KEY=your_ritis_api_key_here
NEWS_API_KEY=your_news_api_key_here

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# LangSmith Monitoring
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=traffix

# RAGAS Evaluation
RAGAS_API_KEY=your_ragas_api_key_here

# System Settings
LOG_LEVEL=INFO
REPORT_OUTPUT_DIR=./reports
STREAMLIT_PORT=8501
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file template")
    else:
        print("✅ .env file exists")


async def main():
    """Main startup function"""
    print("🚦 Traffix - AI Storytelling for Transportation Analytics")
    print("🔧 Enhanced Technology Stack Startup")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    create_directories()
    
    # Check services
    if not check_services():
        print("\n❌ Service checks failed. Please fix the issues above.")
        sys.exit(1)
    
    # Initialize components
    print("\n🚀 Initializing components...")
    
    vector_success = await initialize_vector_database()
    monitoring_success = await initialize_monitoring()
    
    if not vector_success or not monitoring_success:
        print("\n❌ Component initialization failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Traffix startup completed successfully!")
    print("\n📋 Available interfaces:")
    print("   • Streamlit UI: streamlit run streamlit_app.py")
    print("   • FastAPI: python main.py")
    print("   • Demo: python demo.py")
    print("\n🔧 Technology Stack:")
    print("   • LLM: OpenAI GPT-4o")
    print("   • Embeddings: text-embedding-3-large")
    print("   • Orchestration: LangGraph")
    print("   • Vector DB: Qdrant")
    print("   • Monitoring: LangSmith")
    print("   • Evaluation: RAGAS")
    print("   • UI: Streamlit")
    print("\n🚀 Ready to analyze traffic patterns!")


if __name__ == "__main__":
    asyncio.run(main())
