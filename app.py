import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import logging

from config import Config
from core import RAGEngine, DocumentProcessor, VectorStoreManager, SessionManager
from api.routes import api_bp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    
    # Validate configuration
    config_status = Config.validate()
    if not config_status["valid"]:
        logger.error("Configuration validation failed:")
        for issue in config_status["issues"]:
            logger.error(f"  - {issue}")
        if not config_status["config"]["openai_configured"]:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize core components
    logger.info("Initializing Legal Consultation RAG System...")
    
    # Document processor
    document_processor = DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    # Vector store manager
    vector_store_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        openai_api_key=Config.OPENAI_API_KEY
    )
    
    # Load and process documents
    logger.info("Loading and processing documents...")
    documents = document_processor.load_documents(Config.DOCUMENTS_PATH)
    
    if documents:
        logger.info(f"Loaded {len(documents)} document pages")
        chunks = document_processor.chunk_documents(documents)
        logger.info(f"Created {len(chunks)} text chunks")
        
        # Initialize vector store
        if vector_store_manager.initialize_vector_store(chunks):
            logger.info("Vector store initialized successfully")
        else:
            logger.warning("Failed to initialize vector store")
    else:
        logger.warning("No documents found. Vector store will be initialized empty.")
        vector_store_manager.initialize_vector_store([])
    
    # RAG engine
    rag_engine = RAGEngine(
        openai_api_key=Config.OPENAI_API_KEY,
        vector_store_manager=vector_store_manager
    )
    
    # Session manager
    session_manager = SessionManager()
    
    # Attach components to app
    app.document_processor = document_processor
    app.vector_store_manager = vector_store_manager
    app.rag_engine = rag_engine
    app.session_manager = session_manager
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Routes
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
    @app.route('/chat')
    def chat():
        """Chat interface page"""
        return render_template('chat.html')
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {str(error)}")
        return render_template('500.html'), 500
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Basic health check"""
        return jsonify({
            "status": "healthy",
            "service": "Legal Consultation RAG System",
            "version": "1.0.0",
            "timestamp": "2025-08-26T14:45:32Z",
            "developer": "cicada007o"
        })
    
    # Cleanup expired sessions periodically
    @app.before_request
    def cleanup_sessions():
        """Clean up expired sessions before each request"""
        try:
            expired = session_manager.cleanup_expired_sessions(Config.SESSION_TIMEOUT_HOURS)
            if expired > 0:
                logger.info(f"Cleaned up {expired} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
    
    logger.info("Legal Consultation RAG System initialized successfully")
    logger.info(f"Developer: cicada007o | Date: 2025-08-26 14:45:32 UTC")
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Legal Consultation RAG System on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 80)
    logger.info("🚀 LEGAL CONSULTATION RAG SYSTEM")
    logger.info("📚 AI-Powered BNS Legal Document Consultation")
    logger.info("👨‍💻 Developed by: cicada007o")
    logger.info("📅 Date: 2025-08-26 14:45:32 UTC")
    logger.info("🔧 Tech Stack: Python 3.10 + Flask + LangChain + OpenAI + ChromaDB")
    logger.info("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )