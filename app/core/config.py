
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # PostgreSQL
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sales_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))

    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "conversations_db")

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Sales Agent Configuration
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))  # 10 exchanges
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))  # 70%
    MAX_RELEVANT_PRODUCTS: int = int(os.getenv("MAX_RELEVANT_PRODUCTS", "3"))

    # Routing Agent Configuration
    ROUTING_AGENT_URL: str = os.getenv("ROUTING_AGENT_URL", "")
    ROUTING_AGENT_API_KEY: str = os.getenv("ROUTING_AGENT_API_KEY", "")

    # Validation
    def validate_settings(self):
        """Validate that required settings are present"""
        if not self.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY is required")
        if not self.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        
        return True

settings = Settings()
