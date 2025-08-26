// Session Management for Legal Consultation System
// Author: cicada007o
// Date: 2025-08-26

class SessionManager {
    constructor() {
        this.currentSession = null;
        this.sessionData = null;
        this.storageKey = 'legal_consultation_session';
        this.initialize();
    }

    initialize() {
        // Try to restore session from localStorage
        const savedSession = localStorage.getItem(this.storageKey);
        if (savedSession) {
            try {
                const sessionInfo = JSON.parse(savedSession);
                // Check if session is not expired (24 hours)
                const sessionAge = Date.now() - sessionInfo.created;
                if (sessionAge < 24 * 60 * 60 * 1000) {
                    this.currentSession = sessionInfo.sessionId;
                    this.sessionData = sessionInfo;
                    this.updateSessionDisplay();
                    console.log('Session restored:', this.currentSession);
                } else {
                    this.clearSession();
                }
            } catch (error) {
                console.error('Error restoring session:', error);
                this.clearSession();
            }
        }
    }

    async createSession() {
        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: 'Initialize session',
                    session_id: null
                })
            });

            const data = await response.json();
            
            if (data.success && data.session_stats) {
                this.currentSession = data.session_stats.session_id;
                this.sessionData = {
                    sessionId: this.currentSession,
                    created: Date.now(),
                    questionCount: 0,
                    lastActivity: Date.now()
                };
                
                // Save to localStorage
                localStorage.setItem(this.storageKey, JSON.stringify(this.sessionData));
                this.updateSessionDisplay();
                
                console.log('New session created:', this.currentSession);
                return this.currentSession;
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            window.LegalConsultationApp?.showToast?.('Failed to create session', 'danger');
            return null;
        }
    }

    getCurrentSession() {
        return this.currentSession;
    }

    async getSessionStats() {
        if (!this.currentSession) return null;

        try {
            const response = await fetch(`/api/session/${this.currentSession}`);
            const data = await response.json();
            
            if (data.success) {
                return data.session;
            } else {
                console.error('Failed to get session stats:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error getting session stats:', error);
            return null;
        }
    }

    updateSession(questionCount = null) {
        if (this.sessionData) {
            this.sessionData.lastActivity = Date.now();
            if (questionCount !== null) {
                this.sessionData.questionCount = questionCount;
            }
            localStorage.setItem(this.storageKey, JSON.stringify(this.sessionData));
            this.updateSessionDisplay();
        }
    }

    updateSessionDisplay() {
        const sessionInfo = document.getElementById('sessionInfo');
        const sessionIndicator = document.getElementById('sessionIndicator');
        
        if (sessionInfo && this.currentSession) {
            const sessionAge = this.sessionData ? 
                Math.floor((Date.now() - this.sessionData.created) / (1000 * 60)) : 0;
            
            sessionInfo.innerHTML = `
                <div class="mb-2">
                    <strong>Session ID:</strong>
                    <small class="font-monospace text-muted d-block">
                        ${this.currentSession.substring(0, 8)}...
                    </small>
                </div>
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        Active for ${sessionAge} minutes
                    </small>
                </div>
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-comments me-1"></i>
                        Questions: ${this.sessionData?.questionCount || 0}
                    </small>
                </div>
            `;
        } else if (sessionInfo) {
            sessionInfo.innerHTML = `
                <span class="badge bg-secondary">
                    <i class="fas fa-plus me-1"></i>Starting...
                </span>
            `;
        }

        if (sessionIndicator) {
            sessionIndicator.innerHTML = `
                <i class="fas fa-circle me-1"></i>
                Session: ${this.currentSession ? 'Active' : 'Not Started'}
            `;
            sessionIndicator.className = `badge ${this.currentSession ? 'bg-success' : 'bg-secondary'}`;
        }
    }

    async resetSession() {
        try {
            // Call API to reset session
            const response = await fetch('/api/reset-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSession
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.clearSession();
                this.currentSession = data.new_session_id;
                this.sessionData = {
                    sessionId: this.currentSession,
                    created: Date.now(),
                    questionCount: 0,
                    lastActivity: Date.now()
                };
                
                localStorage.setItem(this.storageKey, JSON.stringify(this.sessionData));
                this.updateSessionDisplay();
                
                window.LegalConsultationApp?.showToast?.('New session started', 'success');
                console.log('Session reset, new session:', this.currentSession);
                
                return this.currentSession;
            } else {
                throw new Error(data.error || 'Failed to reset session');
            }
        } catch (error) {
            console.error('Error resetting session:', error);
            window.LegalConsultationApp?.showToast?.('Failed to reset session', 'danger');
            return null;
        }
    }

    clearSession() {
        this.currentSession = null;
        this.sessionData = null;
        localStorage.removeItem(this.storageKey);
        this.updateSessionDisplay();
        console.log('Session cleared');
    }

    exportSession() {
        if (!this.sessionData) {
            window.LegalConsultationApp?.showToast?.('No session to export', 'warning');
            return;
        }

        const exportData = {
            sessionId: this.currentSession,
            created: new Date(this.sessionData.created).toISOString(),
            questionCount: this.sessionData.questionCount,
            lastActivity: new Date(this.sessionData.lastActivity).toISOString(),
            exportedAt: new Date().toISOString(),
            system: 'Legal Consultation RAG System',
            developer: 'cicada007o'
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `legal-session-${this.currentSession.substring(0, 8)}-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        window.LegalConsultationApp?.showToast?.('Session exported successfully', 'success');
    }

    // Get session summary for display
    getSessionSummary() {
        if (!this.sessionData) return null;

        const duration = Math.floor((Date.now() - this.sessionData.created) / (1000 * 60));
        
        return {
            id: this.currentSession,
            shortId: this.currentSession ? this.currentSession.substring(0, 8) + '...' : 'None',
            duration: duration,
            durationText: duration < 60 ? `${duration}m` : `${Math.floor(duration/60)}h ${duration%60}m`,
            questionCount: this.sessionData.questionCount || 0,
            created: new Date(this.sessionData.created).toLocaleString(),
            lastActivity: new Date(this.sessionData.lastActivity).toLocaleString(),
            isActive: this.currentSession !== null
        };
    }
}

// Create global session manager instance
const sessionManager = new SessionManager();

// Global functions for use in HTML
window.resetSession = async function() {
    const confirmed = confirm('Are you sure you want to start a new session? This will clear your current conversation.');
    if (confirmed) {
        await sessionManager.resetSession();
        
        // Clear chat messages if on chat page
        if (typeof clearChatMessages === 'function') {
            clearChatMessages();
        }
        
        // Reload page to refresh chat
        if (window.location.pathname === '/chat') {
            window.location.reload();
        }
    }
};

window.exportSession = function() {
    sessionManager.exportSession();
};

// Auto-save session data periodically
setInterval(() => {
    if (sessionManager.currentSession) {
        sessionManager.updateSession();
    }
}, 30000); // Every 30 seconds

// Update session display periodically
setInterval(() => {
    sessionManager.updateSessionDisplay();
}, 60000); // Every minute

// Export for use by other modules
window.sessionManager = sessionManager;

console.log('Legal Consultation System - Session Manager Loaded');