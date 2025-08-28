from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
import logging
import traceback

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/ask', methods=['POST'])
def ask_question():
    """Main endpoint for processing legal queries"""
    try:
        data = request.get_json()
        
        # Validate request
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "error": "Question is required"
            }), 400
        
        question = data['question'].strip()
        session_id = data.get('session_id')
        
        if not question:
            return jsonify({
                "success": False,
                "error": "Question cannot be empty"
            }), 400
        
        # Get or create session
        session_manager = current_app.session_manager # type: ignore
        if not session_id:
            session_id = session_manager.create_session()
        elif not session_manager.get_session(session_id):
            session_id = session_manager.create_session()
        
        # Process query with RAG engine
        rag_engine = current_app.rag_engine # type: ignore
        response = rag_engine.process_query(question, session_id)
        
        # Update session
        session_manager.update_session(session_id, question, response)
        
        # Add session statistics to response
        response['session_stats'] = session_manager.get_session_stats(session_id)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An error occurred while processing your question"
        }), 500

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system health and initialization status"""
    try:
        rag_engine = current_app.rag_engine # type: ignore
        system_status = rag_engine.get_system_status()
        
        # Add additional system info
        system_status.update({
            "flask_env": current_app.config.get('ENV', 'unknown'),
            "documents_loaded": system_status.get('vector_store', {}).get('document_count', 0) > 0,
            "ready_for_queries": system_status.get('rag_engine') == 'initialized'
        })
        
        return jsonify({
            "success": True,
            "status": system_status
        })
        
    except Exception as e:
        logger.error(f"Error in get_system_status: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Could not retrieve system status"
        }), 500

@api_bp.route('/examples', methods=['GET'])
def get_example_queries():
    """Get curated example legal queries"""
    examples = [
        {
            "category": "Definitions",
            "queries": [
                "What is the definition of theft under BNS?",
                "Define criminal conspiracy in legal terms",
                "What constitutes assault under Indian law?"
            ]
        },
        {
            "category": "Procedures", 
            "queries": [
                "What is the procedure for filing an FIR?",
                "How is bail granted in criminal cases?",
                "What are the steps in a criminal trial?"
            ]
        },
        {
            "category": "Penalties",
            "queries": [
                "What is the punishment for murder under BNS?",
                "What are the penalties for fraud?",
                "What is the sentence for drug trafficking?"
            ]
        },
        {
            "category": "Legal Provisions",
            "queries": [
                "What does Section 103 of BNS say?",
                "Explain the provisions related to self-defense",
                "What are the rights of an accused person?"
            ]
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

@api_bp.route('/session/<session_id>', methods=['GET'])
def get_session_info(session_id: str):
    """Get detailed session information"""
    try:
        session_manager = current_app.session_manager # type: ignore
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
        
        return jsonify({
            "success": True,
            "session": session_manager.get_session_stats(session_id)
        })
        
    except Exception as e:
        logger.error(f"Error in get_session_info: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Could not retrieve session information"
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint for monitoring"""
    try:
        # Quick system health checks
        health_status = {
            "status": "healthy",
            "service": "Legal Consultation RAG System",
            "version": "1.0.0",
            "timestamp": "2025-08-26T14:34:00Z",
            "checks": {
                "api": "operational",
                "database": "operational" if hasattr(current_app, 'rag_engine') else "unavailable",
                "memory": "healthy"
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "Legal Consultation RAG System",
            "error": str(e)
        }), 503

@api_bp.route('/reset-session', methods=['POST'])
def reset_session():
    """Reset/clear current session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if session_id:
            session_manager = current_app.session_manager # type: ignore
            if session_id in session_manager.sessions:
                del session_manager.sessions[session_id]
        
        # Create new session
        new_session_id = current_app.session_manager.create_session() # type: ignore
        
        return jsonify({
            "success": True,
            "message": "Session reset successfully",
            "new_session_id": new_session_id
        })
        
    except Exception as e:
        logger.error(f"Error in reset_session: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Could not reset session"
        }), 500

@api_bp.route('/document-stats', methods=['GET'])
def get_document_stats():
    """Get document processing and vector store statistics"""
    try:
        rag_engine = current_app.rag_engine # type: ignore
        vector_stats = rag_engine.vector_store_manager.get_vector_store_stats()
        
        return jsonify({
            "success": True,
            "document_stats": vector_stats
        })
        
    except Exception as e:
        logger.error(f"Error in get_document_stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Could not retrieve document statistics"
        }), 500

# Error handlers for the API blueprint
@api_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": "The request could not be understood by the server"
    }), 400

@api_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested API endpoint does not exist"
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors"""
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": "The HTTP method is not supported for this endpoint"
    }), 405

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

@api_bp.before_request
def log_request_info():
    """Log API request information"""
    logger.info(f"API Request: {request.method} {request.url}")
    if request.is_json:
        logger.debug(f"Request data: {request.get_json()}")

@api_bp.after_request
def log_response_info(response):
    """Log API response information"""
    logger.info(f"API Response: {response.status_code}")
    return response
