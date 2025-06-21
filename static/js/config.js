// Configuration Helper JavaScript

class ConfigHelper {
    constructor() {
        this.setupEventListeners();
        this.loadServerIP();
    }
    
    setupEventListeners() {
        // Configuration form
        document.getElementById('configForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateConfiguration();
        });
        
        // Network test form
        document.getElementById('testForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.testConnectivity();
        });
        
        // Auto-fill test form with config values
        document.getElementById('serverIp').addEventListener('input', (e) => {
            document.getElementById('testIp').value = e.target.value;
        });
        
        document.getElementById('serverPort').addEventListener('input', (e) => {
            document.getElementById('testPort').value = e.target.value;
        });
    }
    
    loadServerIP() {
        // Auto-detect server IP
        const serverIp = window.location.hostname;
        document.getElementById('serverIp').value = serverIp;
        document.getElementById('testIp').value = serverIp;
    }
    
    async generateConfiguration() {
        const clientType = document.getElementById('clientType').value;
        const serverIp = document.getElementById('serverIp').value;
        const serverPort = parseInt(document.getElementById('serverPort').value);
        
        if (!clientType || !serverIp || !serverPort) {
            this.showAlert('Please fill in all required fields.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/config/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    client_type: clientType,
                    server_ip: serverIp,
                    server_port: serverPort
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate configuration');
            }
            
            const config = await response.json();
            this.displayConfiguration(config);
            
        } catch (error) {
            console.error('Error generating configuration:', error);
            this.showAlert('Failed to generate configuration. Please try again.', 'danger');
        }
    }
    
    displayConfiguration(config) {
        const configOutput = document.getElementById('configOutput');
        const configTitle = document.getElementById('configTitle');
        const configContent = document.getElementById('configContent');
        
        configTitle.innerHTML = `<i class="fas fa-file-code me-2"></i>${config.client_name} Configuration`;
        
        let content = '';
        
        if (config.config_type === 'manual') {
            content = `
                <div class="config-instructions">
                    <h6><i class="fas fa-list-ol me-2"></i>Setup Instructions:</h6>
                    <ol>
                        ${config.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                    </ol>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6><i class="fas fa-cog me-2"></i>Connection Settings:</h6>
                        <div class="config-block">
Server/Domain: ${config.common_settings.domain}
Username: ${config.common_settings.username}
Password: ${config.common_settings.password}
Transport: ${config.common_settings.transport}
Codecs: ${config.common_settings.codecs.join(', ')}
RTP Ports: ${config.common_settings.rtp_port_range}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6><i class="fas fa-phone me-2"></i>Testing Information:</h6>
                        <div class="config-block">
Test Number: ${config.testing.test_number}
Call Duration: ${config.testing.call_duration}
Audio Test: ${config.testing.audio_test}
                        </div>
                    </div>
                </div>
            `;
        } else if (config.config_type === 'file') {
            content = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Save the following content as <strong>${config.filename}</strong>
                </div>
                <div class="config-block">${config.content}</div>
                
                <div class="mt-3">
                    <h6><i class="fas fa-cog me-2"></i>Additional Settings:</h6>
                    <div class="config-block">
Server IP: ${config.server_ip}
Server Port: ${config.server_port}
Username: ${config.common_settings.username}
Password: ${config.common_settings.password}
                    </div>
                </div>
            `;
        }
        
        configContent.innerHTML = content;
        configOutput.style.display = 'block';
        configOutput.scrollIntoView({ behavior: 'smooth' });
    }
    
    async testConnectivity() {
        const testIp = document.getElementById('testIp').value;
        const testPort = parseInt(document.getElementById('testPort').value);
        
        if (!testIp || !testPort) {
            this.showAlert('Please enter IP address and port.', 'warning');
            return;
        }
        
        const testResults = document.getElementById('testResults');
        const testResultsContent = document.getElementById('testResultsContent');
        
        // Show loading state
        testResultsContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                Testing connectivity to ${testIp}:${testPort}...
            </div>
        `;
        testResults.style.display = 'block';
        
        try {
            const response = await fetch('/api/test/connectivity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: testIp,
                    port: testPort
                })
            });
            
            if (!response.ok) {
                throw new Error('Test request failed');
            }
            
            const result = await response.json();
            this.displayTestResults(result);
            
        } catch (error) {
            console.error('Error testing connectivity:', error);
            testResultsContent.innerHTML = `
                <div class="test-result failed">
                    <i class="fas fa-times me-2"></i>
                    <strong>Test Failed:</strong> Unable to perform connectivity test.
                </div>
            `;
        }
    }
    
    displayTestResults(result) {
        const testResultsContent = document.getElementById('testResultsContent');
        
        let content = `
            <div class="mb-3">
                <strong>Target:</strong> ${result.target_ip}:${result.target_port}<br>
                <strong>Test Time:</strong> ${new Date(result.timestamp).toLocaleString()}<br>
                <strong>Overall Status:</strong> 
                <span class="badge bg-${this.getStatusColor(result.overall_status)}">
                    ${result.overall_status.replace('_', ' ').toUpperCase()}
                </span>
            </div>
        `;
        
        Object.entries(result.tests).forEach(([testName, testResult]) => {
            const statusClass = this.getTestResultClass(testResult.status);
            const icon = this.getTestResultIcon(testResult.status);
            
            content += `
                <div class="test-result ${statusClass}">
                    <i class="fas fa-${icon} me-2"></i>
                    <strong>${this.formatTestName(testName)}:</strong> ${testResult.message}
                </div>
            `;
        });
        
        // Add recommendations
        if (result.overall_status !== 'success') {
            content += `
                <div class="mt-3">
                    <h6><i class="fas fa-lightbulb me-2"></i>Troubleshooting Tips:</h6>
                    <ul class="mb-0">
                        <li>Ensure the server is running and accessible</li>
                        <li>Check firewall settings for UDP port ${result.target_port}</li>
                        <li>Verify network connectivity between client and server</li>
                        <li>Try using a different port if the current one is blocked</li>
                    </ul>
                </div>
            `;
        }
        
        testResultsContent.innerHTML = content;
    }
    
    getStatusColor(status) {
        const colorMap = {
            'success': 'success',
            'partial_success': 'warning',
            'failed': 'danger'
        };
        return colorMap[status] || 'secondary';
    }
    
    getTestResultClass(status) {
        const classMap = {
            'success': 'success',
            'failed': 'failed',
            'timeout': 'timeout'
        };
        return classMap[status] || 'failed';
    }
    
    getTestResultIcon(status) {
        const iconMap = {
            'success': 'check',
            'failed': 'times',
            'timeout': 'clock'
        };
        return iconMap[status] || 'times';
    }
    
    formatTestName(testName) {
        return testName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    showAlert(message, type = 'info') {
        // Create and show a temporary alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Global function for copy configuration
function copyConfig() {
    const configContent = document.getElementById('configContent');
    if (!configContent) return;
    
    // Get all text content
    const textContent = configContent.innerText;
    
    // Copy to clipboard
    if (navigator.clipboard) {
        navigator.clipboard.writeText(textContent).then(() => {
            showCopySuccess();
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopyTextToClipboard(textContent);
        });
    } else {
        fallbackCopyTextToClipboard(textContent);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccess();
    } catch (err) {
        console.error('Fallback: Unable to copy', err);
    }
    
    document.body.removeChild(textArea);
}

function showCopySuccess() {
    const button = document.querySelector('[onclick="copyConfig()"]');
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
    button.classList.add('btn-success');
    button.classList.remove('btn-outline-primary');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
        button.classList.add('btn-outline-primary');
    }, 2000);
}

// Initialize configuration helper when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.configHelper = new ConfigHelper();
});
