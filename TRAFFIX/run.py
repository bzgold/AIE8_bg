#!/usr/bin/env python3
"""
Traffix System Runner
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from logging_config import setup_logging
from config import settings
import uvicorn


def main():
    """Main entry point for the Traffix system"""
    print("🚦 Starting Traffix - AI Storytelling for Transportation Analytics")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger("traffix.main")
    
    try:
        # Print configuration
        print(f"📊 Configuration:")
        print(f"   Log Level: {settings.log_level}")
        print(f"   Max Concurrent Agents: {settings.max_concurrent_agents}")
        print(f"   Report Output Directory: {settings.report_output_dir}")
        print(f"   OpenAI API Key: {'✓ Set' if settings.openai_api_key else '✗ Not Set'}")
        print()
        
        # Start the server
        print("🚀 Starting server...")
        print(f"   URL: http://localhost:8000")
        print(f"   API Docs: http://localhost:8000/docs")
        print(f"   Health Check: http://localhost:8000/health")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        logger.info("Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
