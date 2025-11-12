import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    @classmethod
    def validate(cls):
        """Validate that required settings are present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")

# Create a settings instance
settings = Settings()

