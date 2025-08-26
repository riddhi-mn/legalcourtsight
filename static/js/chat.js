// Chat Interface for Legal Consultation System
// Author: cicada007o
// Date: 2025-08-26

class ChatInterface {
    constructor() {
        this.messageCount = 0;
        this.isProcessing = false;
        this.chatHistory = [];
        this.initialize();
    }

    initialize() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.chatForm = document.getElementById('chatForm');

        // Ensure session is created
        if (!sessionManager.getCurrentSession()) {
            sessionManager.createSession();
        }

        console.log('Chat interface initialized');
    }

    async sendMessage(event) {
        if (event) {
            event.preventDefault();
        }

        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing) {
            return;
        }

        this.isProcessing = true;
        this.updateUI(true);

        try {
            // Add user message to chat
            this.addMessage(message, 'user');
            
            // Clear input
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
            document.getElementById('charCount').textContent = '0';

            // Show typing indicator
            this.showTypingIndicator();

            // Get current session or create new one
            let sessionId = sessionManager.getCurrentSession();
            if (!sessionId) {
                sessionId = await sessionManager.createSession();
            }

            // Send request to API
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();

            if (data.success) {
                // Add assistant response
                this.addMessage(data.answer, 'assistant', data);
                
                // Update session
                if (data.session_stats) {
                    sessionManager.updateSession(data.session_stats.question_count);
                }
                
                // Store in chat history
                this.chatHistory.push({
                    question: message,
                    response: data,
                    timestamp: new Date().toISOString()
                });

            } else {
                // Handle error response
                this.addMessage(
                    `I apologize, but I encountered an error: ${data.error || 'Unknown error'}. Please try again.`,
                    'assistant',
                    { confidence: 0, query_type: 'error' },
                    true
                );
                console.error('API Error:', data);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            this.addMessage(
                'I apologize, but I\'m having trouble connecting to the server. Please check your internet connection and try again.',
                'assistant',
                { confidence: 0, query_type: 'error' },
                true
            );
        } finally {
            this.isProcessing = false;
            this.updateUI(false);
            this.scrollToBottom();
        }
    }

    addMessage(content, sender, metadata = null, isError = false) {
        this.messageCount++;
        const timestamp = new Date().toLocaleTimeString();
        
        const messageContainer = document.createElement('div');
        messageContainer.className = `message-container ${sender}-message`;
        messageContainer.id = `message-${this.messageCount}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        messageHeader.innerHTML = `
            <strong>${sender === 'user' ? 'You' : 'Legal AI Assistant'}</strong>
            <span class="message-time">${timestamp}</span>
        `;

        const messageBody = document.createElement('div');
        messageBody.className = `message-body ${isError ? 'message-error' : ''}`;
        
        // Format content (simple markdown-like formatting)
        const formattedContent = this.formatMessageContent(content);
        messageBody.innerHTML = formattedContent;

        messageContent.appendChild(messageHeader);
        messageContent.appendChild(messageBody);

        // Add metadata for assistant messages
        if (sender === 'assistant' && metadata && !isError) {
            const metadataDiv = this.createMetadataSection(metadata);
            messageContent.appendChild(metadataDiv);
        }

        messageContainer.appendChild(avatar);
        messageContainer.appendChild(messageContent);

        this.chatMessages.appendChild(messageContainer);
        this.scrollToBottom();
    }

    formatMessageContent(content) {
        // Basic formatting
        let formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        // Format legal sections
        formatted = formatted.replace(
            /(Section\s+\d+|Sec\.\s+\d+|BNS\s+\d+|Article\s+\d+)/gi,
            '<strong class="text-primary">$1</strong>'
        );

        // Format lists
        if (formatted.includes('•') || formatted.includes('-')) {
            const lines = formatted.split('<br>');
            let inList = false;
            let result = '';
            
            for (let line of lines) {
                line = line.trim();
                if (line.match(/^[•\-]\s/)) {
                    if (!inList) {
                        result += '<ul>';
                        inList = true;
                    }
                    result += `<li>${line.replace(/^[•\-]\s/, '')}</li>`;
                } else {
                    if (inList) {
                        result += '</ul>';
                        inList = false;
                    }
                    result += line ? `<p>${line}</p>` : '';
                }
            }
            if (inList) {
                result += '</ul>';
            }
            formatted = result;
        } else {
            // Wrap in paragraphs if not formatted as list
            const paragraphs = formatted.split('<br><br>');
            formatted = paragraphs.map(p => p.trim() ? `<p>${p.replace(/<br>/g, ' ')}</p>` : '').join('');
        }

        return formatted;
    }

    createMetadataSection(metadata) {
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'response-metadata';

        // Confidence score
        let confidenceClass = 'confidence-low';
        let confidenceText = 'Low';
        if (metadata.confidence >= 0.7) {
            confidenceClass = 'confidence-high';
            confidenceText = 'High';
        } else if (metadata.confidence >= 0.4) {
            confidenceClass = 'confidence-medium';
            confidenceText = 'Medium';
        }

        // Query type badge
        const queryTypeClass = `query-type-${metadata.query_type || 'general'}`;

        let metadataHTML = `
            <div class="metadata-grid">
                <div class="metadata-item">
                    <span class="metadata-label">Confidence:</span>
                    <span class="confidence-score ${confidenceClass}">${confidenceText} (${Math.round((metadata.confidence || 0) * 100)}%)</span>
                </div>
                <div class="metadata-item">
                    <span class="metadata-label">Query Type:</span>
                    <span class="query-type-badge ${queryTypeClass}">${metadata.query_type || 'general'}</span>
                </div>
        `;

        if (metadata.retrieved_docs_count) {
            metadataHTML += `
                <div class="metadata-item">
                    <span class="metadata-label">Sources Found:</span>
                    <span class="metadata-value">${metadata.retrieved_docs_count}</span>
                </div>
            `;
        }

        metadataHTML += `</div>`;

        // BNS Citations
        if (metadata.bns_citations && metadata.bns_citations.length > 0) {
            metadataHTML += `
                <div class="citations-list">
                    <div class="sources-title">BNS Citations:</div>
                    <div>
                        ${metadata.bns_citations.map(citation => 
                            `<span class="citation-item">${citation}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        // Sources
        if (metadata.relevant_excerpts && metadata.relevant_excerpts.length > 0) {
            metadataHTML += `
                <div class="sources-list">
                    <div class="sources-title">Relevant Sources:</div>
                    ${metadata.relevant_excerpts.map(excerpt => `
                        <div class="source-item">
                            <div class="source-file">${excerpt.source}</div>
                            <div class="source-section">${excerpt.legal_section}</div>
                            <div class="source-preview">${excerpt.content}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // View details button
        metadataHTML += `
            <button class="btn btn-outline-info view-details-btn" onclick="showResponseDetails(${this.messageCount}, ${JSON.stringify(metadata).replace(/"/g, '&quot;')})">
                <i class="fas fa-info-circle me-1"></i>View Details
            </button>
        `;

        metadataDiv.innerHTML = metadataHTML;
        return metadataDiv;
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    updateUI(processing) {
        this.sendButton.disabled = processing;
        this.messageInput.disabled = processing;
        
        if (processing) {
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.chatMessages.parentElement.classList.add('chat-loading');
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.chatMessages.parentElement.classList.remove('chat-loading');
            this.messageInput.focus();
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the conversation? This cannot be undone.')) {
            this.clearChatMessages();
            this.chatHistory = [];
            this.messageCount = 0;
            window.LegalConsultationApp?.showToast?.('Conversation cleared', 'info');
        }
    }

    clearChatMessages() {
        // Keep only the welcome message
        const messages = this.chatMessages.querySelectorAll('.message-container');
        messages.forEach((message, index) => {
            if (index > 0) { // Keep first message (welcome)
                message.remove();
            }
        });
        this.messageCount = 1; // Reset to 1 (welcome message)
    }

    exportChat() {
        if (this.chatHistory.length === 0) {
            window.LegalConsultationApp?.showToast?.('No conversation to export', 'warning');
            return;
        }

        const exportData = {
            sessionId: sessionManager.getCurrentSession(),
            exportedAt: new Date().toISOString(),
            messageCount: this.chatHistory.length,
            conversation: this.chatHistory.map((item, index) => ({
                id: index + 1,
                question: item.question,
                answer: item.response.answer,
                confidence: item.response.confidence,
                queryType: item.response.query_type,
                citations: item.response.bns_citations || [],
                sources: item.response.relevant_excerpts || [],
                timestamp: item.timestamp
            })),
            system: 'Legal Consultation RAG System',
            developer: 'cicada007o',
            disclaimer: 'This conversation is for informational purposes only and does not constitute legal advice.'
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const sessionId = sessionManager.getCurrentSession() || 'unknown';
        const exportFileName = `legal-chat-${sessionId.substring(0, 8)}-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileName);
        linkElement.click();
        
        window.LegalConsultationApp?.showToast?.('Chat exported successfully', 'success');
    }

    loadExampleQuery(category) {
        const examples = {
            definitions: "What is the definition of theft under BNS?",
            procedures: "What is the procedure for filing an FIR?",
            penalties: "What is the punishment for murder under BNS?",
            sections: "What does Section 103 of BNS say?"
        };

        const query = examples[category];
        if (query) {
            this.messageInput.value = query;
            this.messageInput.focus();
            this.messageInput.dispatchEvent(new Event('input')); // Trigger character count update
        }
    }
}

// Global functions for HTML onclick handlers
window.sendMessage = function(event) {
    chatInterface.sendMessage(event);
};

window.clearChat = function() {
    chatInterface.clearChat();
};

window.exportChat = function() {
    chatInterface.exportChat();
};

window.clearChatMessages = function() {
    chatInterface.clearChatMessages();
};

window.loadExampleQuery = function(category) {
    chatInterface.loadExampleQuery(category);
};

window.showResponseDetails = function(messageId, metadata) {
    const modal = new bootstrap.Modal(document.getElementById('responseDetailsModal'));
    const modalContent = document.getElementById('responseDetailsContent');
    
    const detailsHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="fw-bold">Response Analysis</h6>
                <table class="table table-sm">
                    <tr>
                        <th>Confidence Score:</th>
                        <td>${Math.round((metadata.confidence || 0) * 100)}%</td>
                    </tr>
                    <tr>
                        <th>Query Type:</th>
                        <td><span class="badge bg-info">${metadata.query_type || 'general'}</span></td>
                    </tr>
                    <tr>
                        <th>Sources Retrieved:</th>
                        <td>${metadata.retrieved_docs_count || 0}</td>
                    </tr>
                    <tr>
                        <th>AI Model:</th>
                        <td>${metadata.model || 'GPT-3.5'}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="fw-bold">Citations & Sources</h6>
                ${metadata.bns_citations && metadata.bns_citations.length > 0 ? `
                    <div class="mb-3">
                        <strong>BNS Citations:</strong><br>
                        ${metadata.bns_citations.map(citation => `<span class="badge bg-primary me-1">${citation}</span>`).join('')}
                    </div>
                ` : ''}
                ${metadata.relevant_excerpts && metadata.relevant_excerpts.length > 0 ? `
                    <div>
                        <strong>Source Documents:</strong><br>
                        ${metadata.relevant_excerpts.map(excerpt => `
                            <small class="d-block text-muted">${excerpt.source} (${excerpt.legal_section})</small>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    modalContent.innerHTML = detailsHTML;
    modal.show();
};

// Initialize chat interface
function initializeChat() {
    if (document.getElementById('chatMessages')) {
        window.chatInterface = new ChatInterface();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

console.log('Legal Consultation System - Chat Interface Loaded');