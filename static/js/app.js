// Comprehensive Iframe Scanner - Frontend JavaScript

class IframeScannerApp {
    constructor() {
        this.socket = null;
        this.currentSessionId = null;
        this.recentScans = JSON.parse(localStorage.getItem('recentScans') || '[]');
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEvents();
        this.updateRecentScans();
        this.updateConnectionStatus(false);
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
            this.showToast('Connected to server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
            this.showToast('Disconnected from server', 'warning');
        });
        
        this.socket.on('status_update', (data) => {
            this.updateProgress(data.progress, data.message);
        });
        
        this.socket.on('log_message', (data) => {
            this.addLogEntry(data.message, data.level, data.timestamp);
        });
        
        this.socket.on('scan_completed', (data) => {
            this.handleScanCompleted(data);
        });
        
        this.socket.on('scan_error', (data) => {
            this.handleScanError(data);
        });
        
        this.socket.on('scan_stopped', (data) => {
            this.handleScanStopped(data);
        });
    }
    
    bindEvents() {
        // Form submission
        document.getElementById('scanForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startScan();
        });
        
        // Input method toggle
        document.querySelectorAll('input[name="inputMethod"]').forEach(radio => {
            radio.addEventListener('change', this.toggleInputMethod.bind(this));
        });
        
        // Clear form
        document.getElementById('clearForm').addEventListener('click', this.clearForm.bind(this));
        
        // Stop scan
        document.getElementById('stopScan').addEventListener('click', this.stopScan.bind(this));
        
        // Clear logs
        document.getElementById('clearLogs').addEventListener('click', this.clearLogs.bind(this));
        
        // New scan
        document.getElementById('newScan').addEventListener('click', this.newScan.bind(this));
        
        // Export results
        document.getElementById('exportResults').addEventListener('click', this.exportResults.bind(this));
        
        // Auto-resize textarea
        const htmlSource = document.getElementById('htmlSource');
        htmlSource.addEventListener('input', this.autoResizeTextarea.bind(this));

        // DOM-only iframe XPath lookup
        const domBtn = document.getElementById('domOnlyBtn');
        if (domBtn) domBtn.addEventListener('click', this.domOnlyLookup.bind(this));
    }
    
    toggleInputMethod() {
        const selectedMethod = document.querySelector('input[name="inputMethod"]:checked').value;
        const urlInput = document.getElementById('urlInput');
        const htmlInput = document.getElementById('htmlInput');
        
        if (selectedMethod === 'url') {
            urlInput.style.display = 'block';
            htmlInput.style.display = 'none';
            document.getElementById('url').required = true;
            document.getElementById('htmlSource').required = false;
        } else {
            urlInput.style.display = 'none';
            htmlInput.style.display = 'block';
            document.getElementById('url').required = false;
            document.getElementById('htmlSource').required = true;
        }
    }
    
    autoResizeTextarea() {
        const textarea = document.getElementById('htmlSource');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 300) + 'px';
    }
    
    async startScan() {
        const formData = new FormData(document.getElementById('scanForm'));
        const selectedMethod = document.querySelector('input[name="inputMethod"]:checked').value;
        
        const data = {
            search_text: formData.get('search_text'),
            headless: document.getElementById('headless').checked
        };
        
        if (selectedMethod === 'url') {
            data.url = formData.get('url');
        } else {
            data.html_source = formData.get('html_source');
        }
        
        // Validate input
        if (!data.search_text.trim()) {
            this.showToast('Please enter search text', 'error');
            return;
        }
        
        if (selectedMethod === 'url' && !data.url.trim()) {
            this.showToast('Please enter a URL', 'error');
            return;
        }
        
        if (selectedMethod === 'html' && !data.html_source.trim()) {
            this.showToast('Please enter HTML source', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/start-scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentSessionId = result.session_id;
                this.socket.emit('join_scan', { session_id: this.currentSessionId });
                this.showProgressSection();
                this.addToRecentScans(data);
                this.showToast('Scan started successfully', 'success');
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showToast(`Error starting scan: ${error.message}`, 'error');
        }
    }
    
    async stopScan() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/stop-scan/${this.currentSessionId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Scan stopped', 'info');
            }
            
        } catch (error) {
            console.error('Error stopping scan:', error);
            this.showToast('Error stopping scan', 'error');
        }
    }
    
    showProgressSection() {
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('startScan').disabled = true;
        this.clearLogs();
        this.updateProgress(0, 'Initializing scan...');
    }
    
    hideProgressSection() {
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('startScan').disabled = false;
    }
    
    updateProgress(percent, message) {
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressMessage = document.getElementById('progressMessage');
        
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressPercent.textContent = `${percent}%`;
        progressMessage.textContent = message;
        
        if (percent === 100) {
            progressBar.classList.remove('progress-bar-animated');
        }
    }
    
    addLogEntry(message, level, timestamp) {
        const logOutput = document.getElementById('logOutput');
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        
        entry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span> ${message}
        `;
        
        logOutput.appendChild(entry);
        logOutput.scrollTop = logOutput.scrollHeight;
    }
    
    clearLogs() {
        document.getElementById('logOutput').innerHTML = '';
    }
    
    async handleScanCompleted(data) {
        this.hideProgressSection();
        
        try {
            const response = await fetch(`/api/scan-results/${data.session_id}`);
            const results = await response.json();
            
            this.displayResults(results);
            this.updateStats(data.summary);
            this.showToast(`Scan completed! Found ${data.summary.total_matches} matches in ${data.summary.total_iframes} iframes`, 'success');
            
        } catch (error) {
            console.error('Error loading results:', error);
            this.showToast('Error loading results', 'error');
        }
    }
    
    handleScanError(data) {
        this.hideProgressSection();
        this.showToast(`Scan failed: ${data.error}`, 'error');
    }
    
    handleScanStopped(data) {
        this.hideProgressSection();
        this.showToast('Scan was stopped', 'info');
    }
    
    displayResults(results) {
        document.getElementById('resultsSection').style.display = 'block';
        
        // Update summary
        this.displayResultsSummary(results.results.summary);
        
        // Display matches
        this.displayMatches(results.results.matches);
        
        // Display iframes
        this.displayIframes(results.results.iframes);
        
        // Update stats
        this.updateStats(results.results.summary);
    }
    
    displayResultsSummary(summary) {
        const summaryContainer = document.getElementById('resultsSummary');
        
        summaryContainer.innerHTML = `
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h4 class="card-title">${summary.total_iframes}</h4>
                        <p class="card-text">Total Iframes</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h4 class="card-title">${summary.accessible_iframes}</h4>
                        <p class="card-text">Accessible</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h4 class="card-title">${summary.inaccessible_iframes}</h4>
                        <p class="card-text">Blocked</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h4 class="card-title">${summary.total_matches}</h4>
                        <p class="card-text">Text Matches</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    displayMatches(matches) {
        const matchesContainer = document.getElementById('matchesContent');
        
        if (matches.length === 0) {
            matchesContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5>No text matches found</h5>
                    <p class="text-muted">The search text was not found in any iframe or the main page.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        matches.forEach((match, index) => {
            html += `
                <div class="result-card match-found fade-in">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h6 class="mb-0">Match #${index + 1}</h6>
                        <span class="status-badge status-found">
                            <i class="fas fa-check-circle"></i> Found
                        </span>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Location:</strong><br>
                            <code>${match.location_path}</code>
                        </div>
                        <div class="col-md-6">
                            <strong>Element:</strong><br>
                            <code>&lt;${match.element_tag}&gt;</code>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <strong>Text Content:</strong><br>
                        <div class="code-display">${this.escapeHtml(match.element_text)}</div>
                    </div>
                    
                    <div class="mt-3">
                        <strong>XPath:</strong><br>
                        <div class="code-display">${this.escapeHtml(match.element_xpath)}</div>
                    </div>
                </div>
            `;
        });
        
        matchesContainer.innerHTML = html;
    }
    
    displayIframes(iframes) {
        const iframesContainer = document.getElementById('iframesContent');
        
        if (iframes.length === 0) {
            iframesContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-window-restore fa-3x text-muted mb-3"></i>
                    <h5>No iframes found</h5>
                    <p class="text-muted">This page does not contain any iframes.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        iframes.forEach((iframe, index) => {
            const statusClass = iframe.accessible ? 'accessible' : 'inaccessible';
            const statusBadge = iframe.accessible ? 'status-accessible' : 'status-blocked';
            const statusIcon = iframe.accessible ? 'fa-check-circle' : 'fa-times-circle';
            const statusText = iframe.accessible ? 'Accessible' : 'Blocked';
            
            html += `
                <div class="iframe-card ${statusClass} fade-in">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h6 class="mb-0">Iframe #${index + 1}</h6>
                        <span class="status-badge ${statusBadge}">
                            <i class="fas ${statusIcon}"></i> ${statusText}
                        </span>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Path:</strong><br>
                            <code>${iframe.path}</code>
                        </div>
                        <div class="col-md-6">
                            <strong>Matches Found:</strong><br>
                            <span class="badge bg-${iframe.matches_found > 0 ? 'success' : 'secondary'}">
                                ${iframe.matches_found}
                            </span>
                        </div>
                    </div>
                    
                    ${iframe.id ? `
                        <div class="mt-2">
                            <strong>ID:</strong> <code>${iframe.id}</code>
                        </div>
                    ` : ''}
                    
                    ${iframe.src ? `
                        <div class="mt-2">
                            <strong>Source:</strong><br>
                            <div class="code-display">${this.escapeHtml(iframe.src)}</div>
                        </div>
                    ` : ''}
                    
                    ${iframe.preview ? `
                        <div class="mt-2">
                            <strong>Content Preview:</strong><br>
                            <div class="code-display">${this.escapeHtml(iframe.preview)}</div>
                        </div>
                    ` : ''}
                    
                    ${iframe.error ? `
                        <div class="mt-2">
                            <strong>Error:</strong><br>
                            <span class="text-danger">${this.escapeHtml(iframe.error)}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        iframesContainer.innerHTML = html;
    }
    
    updateStats(summary) {
        document.getElementById('statIframes').textContent = summary.total_iframes || 0;
        document.getElementById('statMatches').textContent = summary.total_matches || 0;
    }
    
    addToRecentScans(scanData) {
        const scan = {
            id: this.currentSessionId,
            timestamp: new Date().toISOString(),
            searchText: scanData.search_text,
            inputType: scanData.url ? 'URL' : 'HTML',
            input: scanData.url || 'HTML Source'
        };
        
        this.recentScans.unshift(scan);
        this.recentScans = this.recentScans.slice(0, 5); // Keep only last 5
        
        localStorage.setItem('recentScans', JSON.stringify(this.recentScans));
        this.updateRecentScans();
    }
    
    updateRecentScans() {
        const container = document.getElementById('recentScans');
        
        if (this.recentScans.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No recent scans</p>';
            return;
        }
        
        let html = '';
        this.recentScans.forEach(scan => {
            const date = new Date(scan.timestamp);
            const timeStr = date.toLocaleTimeString();
            
            html += `
                <div class="recent-scan-item">
                    <div class="d-flex justify-content-between">
                        <strong>${scan.searchText}</strong>
                        <small class="recent-scan-time">${timeStr}</small>
                    </div>
                    <small class="text-muted">${scan.inputType}: ${scan.input.substring(0, 30)}...</small>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    clearForm() {
        document.getElementById('scanForm').reset();
        document.getElementById('headless').checked = true;
        document.querySelector('input[name="inputMethod"][value="url"]').checked = true;
        this.toggleInputMethod();
    }
    
    newScan() {
        this.hideProgressSection();
        document.getElementById('resultsSection').style.display = 'none';
        this.clearForm();
        this.currentSessionId = null;
    }
    
    exportResults() {
        if (!this.currentSessionId) return;
        
        // This would typically fetch the full results and create a downloadable file
        this.showToast('Export functionality coming soon', 'info');
    }

    async domOnlyLookup() {
        const html = document.getElementById('htmlSource').value || '';
        const searchText = document.getElementById('searchText').value || '';
        if (!html.trim()) {
            this.showToast('Paste HTML/DOM source first', 'warning');
            return;
        }
        if (!searchText.trim()) {
            this.showToast('Enter search text', 'warning');
            return;
        }
        try {
            const res = await fetch('/api/dom-iframe-xpaths', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ html_source: html, search_text: searchText })
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Failed');

            const results = document.getElementById('domOnlyResults');
            const list = document.getElementById('domOnlyList');
            list.innerHTML = '';
            if ((data.xpaths || []).length === 0) {
                list.innerHTML = '<li class="list-group-item small text-muted">No matches in iframe attributes/srcdoc.</li>';
            } else {
                data.xpaths.forEach((xp, i) => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `<code class="small">${this.escapeHtml(xp)}</code><span class="badge bg-primary rounded-pill">${i+1}</span>`;
                    list.appendChild(li);
                });
            }
            results.style.display = 'block';
            this.showToast(`Found ${data.count} iframe XPath${data.count===1?'':'s'}`, 'success');
        } catch (e) {
            this.showToast(`DOM-only lookup failed: ${e.message}`, 'error');
        }
    }
    
    updateConnectionStatus(connected) {
        const statusIcon = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');
        
        if (connected) {
            statusIcon.className = 'fas fa-circle text-success me-1';
            statusText.textContent = 'Connected';
        } else {
            statusIcon.className = 'fas fa-circle text-danger me-1';
            statusText.textContent = 'Disconnected';
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastMessage = document.getElementById('toastMessage');
        const toastHeader = toast.querySelector('.toast-header i');
        
        // Update icon and color based on type
        const iconMap = {
            success: 'fas fa-check-circle text-success',
            error: 'fas fa-exclamation-circle text-danger',
            warning: 'fas fa-exclamation-triangle text-warning',
            info: 'fas fa-info-circle text-primary'
        };
        
        toastHeader.className = iconMap[type] || iconMap.info;
        toastMessage.textContent = message;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new IframeScannerApp();
});
