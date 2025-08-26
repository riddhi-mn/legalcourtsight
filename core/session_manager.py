import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    created_at: str
    question_count: int
    query_history: List[Dict[str, Any]]
    confidence_scores: List[float]
    last_activity: str
    
    @property
    def average_confidence(self) -> float:
        """Calculate average confidence score"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes"""
        created = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        last_activity = datetime.fromisoformat(self.last_activity.replace('Z', '+00:00'))
        return int((last_activity - created).total_seconds() / 60)

class SessionManager:
    """UUID-based session management for legal consultations"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
    
    def create_session(self) -> str:
        """Create new consultation session with UUID"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        session_data = SessionData(
            session_id=session_id,
            created_at=now,
            question_count=0,
            query_history=[],
            confidence_scores=[],
            last_activity=now
        )
        
        self.sessions[session_id] = session_data
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session data"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, query: str, response: Dict[str, Any]) -> None:
        """Update session with new query and response"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.question_count += 1
        session.last_activity = datetime.utcnow().isoformat() + 'Z'
        
        # Add to query history
        session.query_history.append({
            "question_number": session.question_count,
            "query": query,
            "timestamp": session.last_activity,
            "confidence": response.get('confidence', 0.0),
            "query_type": response.get('query_type', 'general')
        })
        
        # Track confidence scores
        if response.get('confidence'):
            session.confidence_scores.append(response['confidence'])
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "question_count": session.question_count,
            "average_confidence": round(session.average_confidence, 2),
            "duration_minutes": session.duration_minutes,
            "last_activity": session.last_activity,
            "query_types": self._get_query_type_distribution(session)
        }
    
    def _get_query_type_distribution(self, session: SessionData) -> Dict[str, int]:
        """Get distribution of query types in session"""
        distribution = {}
        for query in session.query_history:
            query_type = query.get('query_type', 'general')
            distribution[query_type] = distribution.get(query_type, 0) + 1
        return distribution
    
    def cleanup_expired_sessions(self, hours: int = 24) -> int:
        """Remove expired sessions"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
            if last_activity < cutoff:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)