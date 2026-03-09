"""
Configuration management for Lead Scraper System
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class"""
    
    # OpenRouter (LLM API)
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    
    # MongoDB Atlas
    MONGODB_URI = os.getenv('MONGODB_URI')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'lead_scraper')
    
    # Apify
    APIFY_API_KEY = os.getenv('APIFY_API_KEY')
    APIFY_GOOGLE_PLACES_ACTOR = os.getenv('APIFY_GOOGLE_PLACES_ACTOR', 'compass~crawler-google-places')
    
    # Hunter.io
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
    
    # Reddit
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'LeadScraper/1.0')
    
    @staticmethod
    def _is_placeholder(value: str) -> bool:
        """Check if value is a placeholder"""
        if not value:
            return True
        placeholders = ['your_', 'your-', 'xxx', 'placeholder', 'here', 'todo']
        return any(p in value.lower() for p in placeholders)
    
    # LinkedIn
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    
    # ContactOut
    CONTACTOUT_API_KEY = os.getenv('CONTACTOUT_API_KEY')
    
    # Google
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
    
    # Clearbit
    CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY')
    
    # Scraping Settings
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    # LLM Settings
    LLM_MODEL = os.getenv('LLM_MODEL', 'nvidia/nemotron-nano-9b-v2:free')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))
    
    # Perplexity Settings
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'perplexity/sonar')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['OPENROUTER_API_KEY', 'MONGODB_URI']
        missing = []
        invalid = []
        
        for key in required:
            value = getattr(cls, key)
            if not value:
                missing.append(key)
            elif cls._is_placeholder(value):
                invalid.append(key)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        if invalid:
            raise ValueError(f"Invalid placeholder values detected in .env file: {', '.join(invalid)}. Please update with real API keys.")
        return True
    
    @classmethod
    def is_valid_key(cls, key_name: str) -> bool:
        """Check if a specific API key is valid (not placeholder)"""
        value = getattr(cls, key_name, None)
        return value and not cls._is_placeholder(value)


config = Config()
