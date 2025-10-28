"""
Configuration management for Traffix system
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Database Configuration
    database_url: str = "sqlite:///./traffix.db"
    
    # RITIS API Configuration
    ritis_api_key: str = ""
    ritis_base_url: str = "https://api.ritis.org"
    
    # News API Configuration
    news_api_key: str = ""
    
    # Vector Database Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "traffix_embeddings"
    
    # LangSmith Monitoring
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "traffix"
    langsmith_tracing: bool = True
    
    # RAGAS Evaluation
    ragas_api_key: Optional[str] = None
    enable_evaluation: bool = True
    
    # System Configuration
    log_level: str = "INFO"
    max_concurrent_agents: int = 5
    report_output_dir: str = "./reports"
    
    # Agent Configuration
    quick_mode_max_sources: int = 10
    deep_mode_max_sources: int = 50
    analysis_timeout_minutes: int = 30
    
    # Streamlit Configuration
    streamlit_port: int = 8501
    streamlit_host: str = "localhost"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
