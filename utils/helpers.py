import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import html

def format_timestamp(timestamp: Optional[str] = None) -> str:
    """Format timestamp for display"""
    if not timestamp:
        timestamp = datetime.utcnow().isoformat() + 'Z'
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return timestamp

def validate_session_id(session_id: str) -> bool:
    """Validate UUID session ID format"""
    try:
        uuid.UUID(session_id, version=4)
        return True
    except ValueError:
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input for security"""
    if not isinstance(text, str):
        return ""
    
    # HTML escape
    text = html.escape(text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    return text[:1000]

def extract_legal_keywords(text: str) -> list:
    """Extract legal keywords from text"""
    legal_keywords = [
        'section', 'article', 'act', 'law', 'provision', 'statute',
        'criminal', 'civil', 'penalty', 'punishment', 'fine', 'imprisonment',
        'offense', 'crime', 'legal', 'court', 'judge', 'bail', 'trial'
    ]
    
    found_keywords = []
    text_lower = text.lower()
    
    for keyword in legal_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords

def calculate_reading_time(text: str) -> int:
    """Calculate estimated reading time in minutes"""
    words = len(text.split())
    # Average reading speed: 200 words per minute
    minutes = max(1, words // 200)
    return minutes

def format_legal_response(response: str) -> str:
    """Format legal response with proper structure"""
    # Add line breaks for better readability
    response = response.replace('. ', '.\n\n')
    
    # Format section references
    response = re.sub(r'Section (\d+)', r'**Section \1**', response)
    
    return response