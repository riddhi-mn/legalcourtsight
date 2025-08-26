// Main JavaScript file for the Legal Consultation System
// Author: cicada007o
// Date: 2025-08-26

// Global variables
let systemStatus = null;
let exampleQueries = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Legal Consultation System - Frontend Initialized');
    console.log('Developer: cicada007o | Date: 2025-08-26 14:40:56 UTC');
    
    // Initialize components
    initializeNavbar();
    initializeModals();
    initializeTooltips();
    
    // Load data if on index page
    if (document.getElementById('systemStatusCards')) {
        loadSystemStatus();
    }
    
    if (document.getElementById('exampleQueries')) {
        loadExampleQueries();
    }
    
    // Set up periodic status updates
    setInterval(updateMiniStatus, 60000); // Every minute
});

// Navbar functionality
function initializeNavbar() {
    // Handle navbar collapse on mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close navbar when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInsideNav = navbarCollapse.contains(event.target) || navbarToggler.contains(event.target);
            if (!isClickInsideNav && navbarCollapse.classList.contains('show')) {
                navbarToggler.click();
            }
        });
    }
    
    // Active page highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Modal initialization
function initializeModals() {
    // System Status Modal
    const statusModal = document.getElementById('statusModal');
    if (statusModal) {
        statusModal.addEventListener('show.bs.modal', function() {
            loadSystemStatus();
        });
    }
    
    // Auto-show disclaimer on first visit
    if (localStorage.getItem('disclaimerShown') !== 'true') {
        setTimeout(() => {
            const disclaimerModal = new bootstrap.Modal(document.getElementById('disclaimerModal'));
            disclaimerModal.show();
            localStorage.setItem('disclaimerShown', 'true');
        }, 3000);
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Load and display system status
async function loadSystemStatus() {
    const statusContainer = document.getElementById('systemStatusCards') || document.getElementById('systemStatus');
    
    if (!statusContainer) return;
    
    try {
        // Show loading state
        statusContainer.innerHTML = `
            <div class="col-12 text-center">
                <div class="d-flex justify-content-center align-items-center" style="height: 100px;">
                    <div class="spinner-border text-primary me-3" role="status"></div>
                    <span>Loading system status...</span>
                </div>
            </div>
        `;
        
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.success) {
            systemStatus = data.status;
            displaySystemStatus(data.status, statusContainer);
        } else {
            throw new Error(data.error || 'Failed to load system status');
        }
        
    } catch (error) {
        console.error('Error loading system status:', error);
        statusContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error loading system status:</strong> ${error.message}
                </div>
            </div>
        `;
    }
}

// Display system status cards
function displaySystemStatus(status, container) {
    const ragStatus = status.rag_engine === 'initialized';
    const vectorStatus = status.vector_store?.status === 'initialized';
    const documentsLoaded = status.documents_loaded;
    
    const statusHTML = `
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-robot fa-2x ${ragStatus ? 'text-success' : 'text-warning'} mb-2"></i>
                    <h6 class="card-title">RAG Engine</h6>
                    <span class="badge ${ragStatus ? 'bg-success' : 'bg-warning'}">
                        ${ragStatus ? 'Ready' : 'Initializing'}
                    </span>
                    <div class="mt-2">
                        <small class="text-muted">Model: ${status.llm_model || 'GPT-3.5'}</small>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-database fa-2x ${vectorStatus ? 'text-success' : 'text-warning'} mb-2"></i>
                    <h6 class="card-title">Vector Store</h6>
                    <span class="badge ${vectorStatus ? 'bg-success' : 'bg-warning'}">
                        ${vectorStatus ? 'Connected' : 'Loading'}
                    </span>
                    <div class="mt-2">
                        <small class="text-muted">
                            Documents: ${status.vector_store?.document_count || 0}
                        </small>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-brain fa-2x ${documentsLoaded ? 'text-success' : 'text-info'} mb-2"></i>
                    <h6 class="card-title">AI Model</h6>
                    <span class="badge ${documentsLoaded ? 'bg-success' : 'bg-info'}">
                        ${documentsLoaded ? 'Ready' : 'Standby'}
                    </span>
                    <div class="mt-2">
                        <small class="text-muted">OpenAI GPT-3.5</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = statusHTML;
    
    // Update mini status if exists
    updateMiniStatus();
}

// Update mini status indicator
function updateMiniStatus() {
    const miniStatus = document.getElementById('miniSystemStatus');
    const sessionIndicator = document.getElementById('sessionIndicator');
    
    if (miniStatus && systemStatus) {
        const ready = systemStatus.ready_for_queries;
        miniStatus.innerHTML = `
            <div class="status-indicator">
                <span class="status-dot ${ready ? 'bg-success' : 'bg-warning'}"></span>
                <small>${ready ? 'System Ready' : 'Initializing'}</small>
            </div>
        `;
    }
    
    if (sessionIndicator) {
        const sessionId = sessionManager.getCurrentSession();
        sessionIndicator.innerHTML = `
            <i class="fas fa-circle me-1"></i>
            Session: ${sessionId ? 'Active' : 'Not Started'}
        `;
        sessionIndicator.className = `badge ${sessionId ? 'bg-success' : 'bg-secondary'}`;
    }
}

// Load example queries
async function loadExampleQueries() {
    const container = document.getElementById('exampleQueries');
    if (!container) return;
    
    try {
        const response = await fetch('/api/examples');
        const data = await response.json();
        
        if (data.success) {
            exampleQueries = data.examples;
            displayExampleQueries(data.examples, container);
        } else {
            throw new Error(data.error || 'Failed to load examples');
        }
        
    } catch (error) {
        console.error('Error loading example queries:', error);
        // Keep default examples in HTML if API fails
    }
}

// Display example queries
function displayExampleQueries(examples, container) {
    const colors = ['primary', 'success', 'warning', 'info'];
    const icons = ['book', 'list-ol', 'gavel', 'section'];
    
    let html = '';
    
    examples.forEach((category, index) => {
        const color = colors[index % colors.length];
        const icon = icons[index % icons.length];
        
        category.queries.forEach((query, queryIndex) => {
            if (queryIndex === 0) { // Only show first query from each category
                const encodedQuery = encodeURIComponent(query);
                html += `
                    <div class="col-md-6 col-lg-3">
                        <div class="card h-100 example-card">
                            <div class="card-body">
                                <h6 class="card-title text-${color}">
                                    <i class="fas fa-${icon} me-2"></i>${category.category}
                                </h6>
                                <p class="card-text small">"${query}"</p>
                                <a href="/chat?q=${encodedQuery}" class="btn btn-outline-${color} btn-sm">
                                    <i class="fas fa-arrow-right me-1"></i>Try This
                                </a>
                            </div>
                        </div>
                    </div>
                `;
            }
        });
    });
    
    // Add call-to-action
    html += `
        <div class="col-12 mt-4 text-center">
            <a href="/chat" class="btn btn-primary btn-lg">
                <i class="fas fa-comments me-2"></i>Start Your Legal Consultation
            </a>
        </div>
    `;
    
    container.innerHTML = html;
}

// Utility functions
function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    } catch (error) {
        return timestamp;
    }
}

function showToast(message, type = 'info') {
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check' : type === 'danger' ? 'times' : 'info'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add to toast container or create one
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // Remove element after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }).catch(function() {
        showToast('Failed to copy to clipboard', 'danger');
    });
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    
    // Show user-friendly error message for critical errors
    if (event.error && event.error.message.includes('fetch')) {
        showToast('Network error. Please check your connection.', 'danger');
    }
});

// Export functions for use by other scripts
window.LegalConsultationApp = {
    loadSystemStatus,
    loadExampleQueries,
    formatTimestamp,
    showToast,
    copyToClipboard
};

console.log('Legal Consultation System - Main JS Loaded Successfully');