import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Base settings
    APP_NAME: str = "Build5 Backend"
    DEBUG: bool = False
    
    # File system settings
    FS_BASE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    # API settings
    API_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000, http://localhost:3001"
    
    # MCP settings
    MCP_ENABLED: bool = True
    MCP_PREFIX: str = "/mcp"
    
    # External services
    OPENWEATHERMAP_API_KEY: str = ""

    # Google GenAI settings
    GEMINI_API_KEY: str = ""
    
    # Embedding model
    EMBEDDING_MODEL: str 
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    # Azure OpenAI settings
    GEMINI_CLIENT: str = "gemini-2.5-flash"
# Create global settings instance
settings = Settings()