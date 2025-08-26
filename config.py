import os
from typing import Dict, Any

class Config:
    """Application configuration management"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'legal-consultation-rag-secret-key')
    
    # Application Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', os.path.join(BASE_DIR, 'data', 'vector_store'))
    DOCUMENTS_PATH = os.getenv('DOCUMENTS_PATH', os.path.join(BASE_DIR, 'data', 'documents'))
    
    # RAG Configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
    MAX_RETRIEVAL_DOCS = int(os.getenv('MAX_RETRIEVAL_DOCS', '5'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
    
    # Session Configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
    
    @staticmethod
    def validate() -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        if not Config.OPENAI_API_KEY:
            issues.append("OpenAI API key not configured")
        
        if not os.path.exists(Config.DOCUMENTS_PATH):
            os.makedirs(Config.DOCUMENTS_PATH, exist_ok=True)
            issues.append("Documents directory created")
        
        if not os.path.exists(Config.VECTOR_DB_PATH):
            os.makedirs(Config.VECTOR_DB_PATH, exist_ok=True)
        
        return {
            "valid": len([i for i in issues if "not configured" in i]) == 0,
            "issues": issues,
            "config": {
                "openai_configured": bool(Config.OPENAI_API_KEY),
                "documents_path": Config.DOCUMENTS_PATH,
                "vector_db_path": Config.VECTOR_DB_PATH
            }
        }