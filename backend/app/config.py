from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env or environment variables."""
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"
    
    # Security
    SECRET_KEY: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
